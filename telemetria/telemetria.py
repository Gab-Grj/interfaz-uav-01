import asyncio
import math
import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Dict

# MAVSDK opcional
MAVSDK_OK = True
try:
    from mavsdk import System
except Exception:
    MAVSDK_OK = False

# Serial asíncrono para LoRa
try:
    import serial_asyncio  # pyserial-asyncio
    SERIAL_OK = True
except Exception:
    SERIAL_OK = False


@dataclass
class TelemetrySample:
    time_s: float
    # navegación / actitud / vel
    lat_deg: Optional[float] = None
    lon_deg: Optional[float] = None
    abs_alt_m: Optional[float] = None
    rel_alt_m: Optional[float] = None
    roll_deg: Optional[float] = None
    pitch_deg: Optional[float] = None
    yaw_deg: Optional[float] = None
    vx_ms: Optional[float] = None
    vy_ms: Optional[float] = None
    vz_ms: Optional[float] = None
    groundspeed_ms: Optional[float] = None
    # energía
    voltage_v: Optional[float] = None
    battery_percent: Optional[float] = None
    # estado
    flight_mode: Optional[str] = None
    in_air: Optional[bool] = None
    gps_fix_type: Optional[int] = None
    num_sat: Optional[int] = None
    # ambientales
    temp_c: Optional[float] = None
    hum_pct: Optional[float] = None
    pres_hpa: Optional[float] = None
    rad_mwcm2: Optional[float] = None
    acc_ms2: Optional[float] = None
    # contrato crudo (guardado en historial)
    raw_line: Optional[str] = None


# ----------------------------------------------------------------------
#  BackendTelemetria: DEMO o MAVSDK
# ----------------------------------------------------------------------
class BackendTelemetria:
    """
    Si MAVSDK está instalado y force_demo=False -> telemetría real.
    Si force_demo=True -> telemetría sintética.
    Si force_demo=None -> decide por MAVSDK_OK.
    """

    def __init__(self, force_demo: Optional[bool] = None) -> None:
        if force_demo is None:
            self.is_demo = not MAVSDK_OK
        else:
            self.is_demo = force_demo

        if not self.is_demo and MAVSDK_OK:
            self.system: System = System()

        self._running: bool = False

    async def connect(self, endpoint: str, timeout_s: float = 10.0) -> None:
        """
        Conectarse al backend:
        - DEMO: sólo marca _running = True
        - MAVSDK: se conecta a PX4/Ardupilot vía MAVSDK
        """
        if self.is_demo:
            self._running = True
            return

        # Telemetría real vía MAVSDK
        await self.system.connect(system_address=endpoint)

        # Espera a estar conectado
        async for st in self.system.core.connection_state():
            if st.is_connected:
                break

        # Espera algo de health como sanity check
        async def _health():
            async for h in self.system.telemetry.health():
                return h

        _ = await asyncio.wait_for(_health(), timeout=timeout_s)
        self._running = True

    async def samples(self) -> AsyncIterator[TelemetrySample]:
        """
        Iterador asíncrono que produce TelemetrySample en DEMO o MAVSDK.
        """
        if not self._running:
            # en caso de que se llame sin conectar, intenta DEMO por defecto
            await self.connect("udp://:14540")

        # ---------------------- DEMO ----------------------
        if self.is_demo:
            t0 = time.perf_counter()
            phi = 0.0
            while self._running:
                t = time.perf_counter() - t0

                # Trayectoria circular pequeña alrededor de FI-UNAM
                lat0, lon0 = 19.332, -99.184
                r = 0.0005  # ~50 m
                lat = lat0 + r * math.cos(phi)
                lon = lon0 + r * math.sin(phi)

                rel_alt = 30.0 + 10.0 * math.sin(0.25 * phi)
                roll = 8.0 * math.sin(0.6 * phi)
                pitch = 4.0 * math.cos(0.5 * phi)
                yaw = (phi * 30.0) % 360.0

                vn = 2.0 * math.cos(phi)
                ve = 2.0 * math.sin(phi)
                vd = -0.2 * math.sin(0.2 * phi)
                gs = math.sqrt(vn * vn + ve * ve + vd * vd)

                vbat = 15.8 - 0.0015 * t
                bat = max(0.0, 100.0 - 0.5 * t)

                # Ambientales suaves
                temp = 24.0 + 0.8 * math.sin(0.05 * t)
                hum = 45.0 + 8.0 * math.cos(0.03 * t)
                pres = 1012.0 + 1.0 * math.sin(0.01 * t)
                rad = 0.25 + 0.05 * math.sin(0.07 * t)
                acc = 0.3 + 0.2 * abs(math.sin(0.4 * t))

                line = (
                    f"temp:{temp:.1f},hum:{hum:.1f},pres:{pres:.1f},rad:{rad:.2f},"
                    f"lat:{lat:.4f},lon:{lon:.4f},speed:{gs:.2f},acc:{acc:.2f},ts:{t:.1f}"
                )

                yield TelemetrySample(
                    time_s=t,
                    lat_deg=lat,
                    lon_deg=lon,
                    abs_alt_m=2240.0 + rel_alt,
                    rel_alt_m=rel_alt,
                    roll_deg=roll,
                    pitch_deg=pitch,
                    yaw_deg=yaw,
                    vx_ms=vn,
                    vy_ms=ve,
                    vz_ms=vd,
                    groundspeed_ms=gs,
                    voltage_v=vbat,
                    battery_percent=bat,
                    flight_mode="DEMO",
                    in_air=True,
                    gps_fix_type=3,
                    num_sat=12,
                    temp_c=temp,
                    hum_pct=hum,
                    pres_hpa=pres,
                    rad_mwcm2=rad,
                    acc_ms2=acc,
                    raw_line=line,
                )

                phi += 0.15
                await asyncio.sleep(0.1)

            return  # por si alguien sale del while

        # ---------------------- MAVSDK real ----------------------
        last = TelemetrySample(time_s=0.0)
        t0 = time.perf_counter()

        async def _att():
            async for a in self.system.telemetry.attitude_euler():
                last.roll_deg = a.roll_deg
                last.pitch_deg = a.pitch_deg
                last.yaw_deg = a.yaw_deg

        async def _vel():
            async for v in self.system.telemetry.velocity_ned():
                last.vx_ms = v.north_m_s
                last.vy_ms = v.east_m_s
                last.vz_ms = v.down_m_s
                if None not in (v.north_m_s, v.east_m_s, v.down_m_s):
                    last.groundspeed_ms = (
                        v.north_m_s**2 + v.east_m_s**2 + v.down_m_s**2
                    ) ** 0.5

        async def _bat():
            async for b in self.system.telemetry.battery():
                last.voltage_v = b.voltage_v
                last.battery_percent = (
                    b.remaining_percent * 100.0 if b.remaining_percent is not None else None
                )

        async def _gps():
            async for g in self.system.telemetry.gps_info():
                last.gps_fix_type = int(getattr(g.fix_type, "value", 0))
                last.num_sat = g.num_satellites

        async def _mode():
            async for fm in self.system.telemetry.flight_mode():
                last.flight_mode = fm.name

        async def _air():
            async for s in self.system.telemetry.in_air():
                last.in_air = bool(s)

        # Lanza tareas en paralelo
        asyncio.create_task(_att())
        asyncio.create_task(_vel())
        asyncio.create_task(_bat())
        asyncio.create_task(_gps())
        asyncio.create_task(_mode())
        asyncio.create_task(_air())

        async for p in self.system.telemetry.position():
            last.time_s = time.perf_counter() - t0
            last.lat_deg = p.latitude_deg
            last.lon_deg = p.longitude_deg
            last.abs_alt_m = p.absolute_altitude_m
            last.rel_alt_m = getattr(p, "relative_altitude_m", None)

            # Contrato parcial (sin espacios, minúsculas)
            parts = []

            def add(k, v):
                if v is not None:
                    if isinstance(v, float):
                        parts.append(f"{k}:{v:.4f}")
                    else:
                        parts.append(f"{k}:{v}")

            add("lat", last.lat_deg)
            add("lon", last.lon_deg)
            add("speed", last.groundspeed_ms)
            add("vbat", last.voltage_v)
            add("bat", last.battery_percent)
            add("ts", last.time_s)
            last.raw_line = ",".join(parts)

            yield last

    async def stop(self) -> None:
        """Detiene el backend de telemetría."""
        self._running = False


# ----------------------------------------------------------------------
#  LoRaBackend: lee contrato por puerto serie
# ----------------------------------------------------------------------
class LoRaBackend:
    """
    Lee de un puerto serial (LoRa) líneas:
      clave:valor,clave:valor,...\\n
    Claves esperadas: temp,hum,pres,rad,lat,lon,speed,acc,ts, vbat, bat (sin espacios, minúsculas).
    """

    def __init__(self, port: str, baud: int = 57600) -> None:
        self.port = port
        self.baud = baud
        self._running: bool = False
        self._reader: Optional[asyncio.StreamReader] = None

    async def connect(self, _: str, timeout_s: float = 10.0) -> None:
        if not SERIAL_OK:
            raise RuntimeError(
                "pyserial-asyncio no está instalado. Revisa requirements.txt"
            )

        try:
            self._reader, _ = await serial_asyncio.open_serial_connection(
                url=self.port, baudrate=self.baud
            )
        except Exception as e:
            raise RuntimeError(f"No se pudo abrir {self.port}@{self.baud}: {e}") from e

        self._running = True

    async def samples(self) -> AsyncIterator[TelemetrySample]:
        if not self._running:
            await self.connect(self.port)

        t0 = time.perf_counter()

        while self._running:
            try:
                line_bytes = await asyncio.wait_for(
                    self._reader.readline(), timeout=2.0
                )
            except asyncio.TimeoutError:
                continue

            if not line_bytes:
                continue

            try:
                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                data = self._parse_line(line)

                if data.get("ts") is not None:
                    t = float(data.get("ts"))
                else:
                    t = time.perf_counter() - t0

                def f(key: str) -> Optional[float]:
                    try:
                        v = data.get(key)
                        return float(v) if v is not None else None
                    except Exception:
                        return None

                lat = f("lat")
                lon = f("lon")
                spd = f("speed")
                acc = f("acc")
                temp = f("temp")
                hum = f("hum")
                pres = f("pres")
                rad = f("rad")
                vbat = f("vbat")
                batp = f("bat")

                yield TelemetrySample(
                    time_s=t,
                    lat_deg=lat,
                    lon_deg=lon,
                    abs_alt_m=None,
                    rel_alt_m=None,
                    roll_deg=None,
                    pitch_deg=None,
                    yaw_deg=None,
                    vx_ms=None,
                    vy_ms=None,
                    vz_ms=None,
                    groundspeed_ms=spd,
                    voltage_v=vbat,
                    battery_percent=batp,
                    flight_mode="LORA",
                    in_air=None,
                    gps_fix_type=None,
                    num_sat=None,
                    temp_c=temp,
                    hum_pct=hum,
                    pres_hpa=pres,
                    rad_mwcm2=rad,
                    acc_ms2=acc,
                    raw_line=line,  # guardamos EXACTAMENTE lo que llega
                )
            except Exception:
                # Si llega basura, la ignoramos
                continue

    @staticmethod
    def _parse_line(line: str) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for part in line.split(","):
            if ":" not in part:
                continue
            k, v = part.split(":", 1)
            k = k.strip().lower()
            v = v.strip()
            try:
                out[k] = float(v)
            except Exception:
                # Ignora valores no numéricos
                pass
        return out

    async def stop(self) -> None:
        """Detiene la lectura por LoRa."""
        self._running = False
