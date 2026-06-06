#!/usr/bin/env python3
# =============================================================================
#  ANALIZADOR DE DISIPACIÓN TÉRMICA — CPU
#  Termodinámica Aplicada | Universidad de Cartagena
#  Física I — Mecánica y Termodinámica
#
#  Objetivo: Determinar la capacidad de disipación térmica necesaria
#  para mantener el CPU dentro de su temperatura máxima de operación.
#
#  Fórmula central (Fourier — conducción en serie):
#    T_j = T_entrada + Q × (R_jc + R_pasta + R_sistema)
#    Despejando R_sistema:
#    R_sis_max = (Tj_max - T_entrada) / Q  −  R_jc  −  R_pasta
# =============================================================================

import os, glob

R_ = "\033[91m"; G  = "\033[92m"; Y  = "\033[93m"; B  = "\033[94m"
C  = "\033[96m"; M  = "\033[95m"; W  = "\033[97m"; D  = "\033[2m"; RS = "\033[0m"

# ── CPUs portátil: (nombre, TDP_base W, TDP_boost W, Tj_max °C, R_jc °C/W, R_sis_fab °C/W)
CPUS_LAPTOP = {
    "1":  ("Intel Core i3-1215U",    15,  29, 100, 0.55, 0.55),
    "2":  ("Intel Core i5-1235U",    15,  55, 100, 0.50, 0.50),
    "3":  ("Intel Core i5-1335U",    15,  55, 100, 0.48, 0.48),
    "4":  ("Intel Core i5-12450H",   45,  95, 100, 0.38, 0.42),
    "5":  ("Intel Core i5-11245H",   35,  80, 100, 0.38, 0.42),
    "6":  ("Intel Core i7-1255U",    15,  55, 100, 0.45, 0.45),
    "7":  ("Intel Core i7-1355U",    15,  55, 100, 0.43, 0.43),
    "8":  ("Intel Core i7-12700H",   45, 115, 100, 0.28, 0.32),
    "9":  ("Intel Core i9-13900H",   45, 115, 100, 0.25, 0.30),
    "10": ("AMD Ryzen 5 5500U",      15,  35,  95, 0.50, 0.52),
    "11": ("AMD Ryzen 5 7530U",      15,  54,  95, 0.48, 0.50),
    "12": ("AMD Ryzen 5 7640U",      15,  54,  95, 0.45, 0.48),
    "13": ("AMD Ryzen 7 5800H",      45,  54,  95, 0.32, 0.38),
    "14": ("AMD Ryzen 7 7735H",      45,  54,  95, 0.30, 0.35),
    "15": ("AMD Ryzen 9 7940HS",     35,  54,  95, 0.30, 0.35),
    "16": ("Apple M2",               10,  20, 110, 0.40, 0.38),
    "17": ("Apple M3 Pro",           30,  40, 110, 0.35, 0.33),
    "18": ("Personalizado",           0,   0,   0, 0.00, 0.00),
}

# ── GPUs dedicadas portátil: (nombre, TDP_base W, TDP_max W, Tj_max °C, R_gpu_jc °C/W)
GPUS_LAPTOP = {
    "1":  ("NVIDIA GeForce MX450",         25,  35,  97, 0.60),
    "2":  ("NVIDIA GeForce MX550",         25,  35,  97, 0.58),
    "3":  ("NVIDIA GeForce RTX 3050 (laptop)", 35, 80,  97, 0.45),
    "4":  ("NVIDIA GeForce RTX 3060 (laptop)", 60, 115, 97, 0.35),
    "5":  ("NVIDIA GeForce RTX 3070 (laptop)", 80, 125, 97, 0.30),
    "6":  ("NVIDIA GeForce RTX 4050 (laptop)", 35, 115, 97, 0.42),
    "7":  ("NVIDIA GeForce RTX 4060 (laptop)", 35, 115, 97, 0.38),
    "8":  ("NVIDIA GeForce RTX 4070 (laptop)", 35, 150, 97, 0.32),
    "9":  ("AMD Radeon RX 6600M",          50, 100,  100, 0.40),
    "10": ("AMD Radeon RX 7600M XT",       60, 120,  100, 0.38),
    "11": ("Intel Arc A370M",              35,  50,  100, 0.50),
    "12": ("Personalizada",                 0,   0,    0, 0.00),
}

# ── CPUs escritorio: (nombre, TDP W, Tj_max °C, R_jc °C/W)
CPUS_DESKTOP = {
    "1":  ("Intel Core i3-12100",     60, 100, 0.30),
    "2":  ("Intel Core i5-12400",     65, 100, 0.25),
    "3":  ("Intel Core i5-13600K",   125, 100, 0.20),
    "4":  ("Intel Core i7-12700K",   125, 100, 0.18),
    "5":  ("Intel Core i7-13700K",   125, 100, 0.17),
    "6":  ("Intel Core i9-13900K",   253, 100, 0.12),
    "7":  ("AMD Ryzen 5 5600",        65,  95, 0.28),
    "8":  ("AMD Ryzen 5 7600X",      105,  95, 0.22),
    "9":  ("AMD Ryzen 7 5800X",      105,  95, 0.22),
    "10": ("AMD Ryzen 9 5900X",      105,  95, 0.18),
    "11": ("AMD Ryzen 9 7900X",      170,  95, 0.15),
    "12": ("Personalizado",            0,   0, 0.00),
}

# ── Pastas: (nombre, R °C/W, k W/m·K)
PASTAS = {
    "1": ("Pasta de fábrica nueva",              0.40,  4.0),
    "2": ("Pasta de fábrica degradada (>2 años)",0.60,  2.5),
    "3": ("Pasta genérica de tienda",            0.45,  3.5),
    "4": ("Arctic MX-4 / MX-6",                 0.20,  8.5),
    "5": ("Noctua NT-H1 / NT-H2",               0.18,  8.9),
    "6": ("Thermal Grizzly Kryonaut",            0.12, 12.5),
    "7": ("Thermal Grizzly Conductonaut (metal)",0.05, 73.0),
    "8": ("Sin pasta — contacto seco (MUY MALO)",5.00,  0.3),
}

# ── Sistemas de disipación portátil: (nombre, R_sis °C/W, descripcion)
# Estos son los rangos reales medidos de sistemas integrados de laptops
SISTEMAS_LAPTOP = {
    "1": ("Sistema de fábrica (pasta nueva, ventilador limpio)",      0.40,
          "Estado original del portátil recién comprado"),
    "2": ("Sistema actual estimado (pasta fábrica, algo de polvo)",   0.55,
          "Portátil con 1-3 años de uso sin mantenimiento"),
    "3": ("Sistema degradado (pasta envejecida, polvo acumulado)",    0.75,
          "Portátil con >3 años, ventilador sucio, pasta seca"),
    "4": ("Sistema con base activa (+ventiladores externos)",         0.30,
          "Laptop elevada sobre base con ventiladores adicionales"),
    "5": ("Sistema con repaste (pasta premium) + base activa",        0.25,
          "Mejor configuración posible sin abrir el portátil"),
    "6": ("Personalizado",                                            0.00, ""),
}

# ── Disipadores escritorio: (nombre, R °C/W, tipo, precio_usd)
DISIPADORES_DESKTOP = [
    ("Stock Intel/AMD (incluido en caja)",       2.50, "Aire",     0),
    ("Torre económica 1 fan 92mm",               1.20, "Aire",    15),
    ("Torre gama media 1 fan 120mm",             0.80, "Aire",    30),
    ("Torre gama media 2 fans 140mm",            0.60, "Aire",    45),
    ("Noctua NH-U12S / be quiet! DRP4",          0.50, "Aire",    65),
    ("Noctua NH-D15 / be quiet! DRP5",           0.35, "Aire",    90),
    ("AIO 120mm (refrigeración líquida)",        0.45, "Líquido", 70),
    ("AIO 240mm (refrigeración líquida)",        0.30, "Líquido",110),
    ("AIO 360mm (refrigeración líquida)",        0.20, "Líquido",140),
    ("Custom loop (loop personalizado)",         0.12, "Líquido",300),
]

# ── Superficies de uso (portátil)
SUPERFICIES = {
    "1": ("Mesa dura (madera/vidrio/metal)",     0),
    "2": ("Base activa con ventiladores",       -6),
    "3": ("Soporte rígido sin ventiladores",    -2),
    "4": ("Regazo / falda sobre ropa",         +12),
    "5": ("Cama / almohada / sofá blando",     +20),
    "6": ("Superficie irregular / mochila",    +10),
}

# ─────────────────────────────────────────────────────────────────────────────
def limpiar(): os.system("clear" if os.name == "posix" else "cls")

def titulo(t):
    l = "═" * 64
    print(f"\n{C}{l}\n  {W}{t}{C}\n{l}{RS}\n")

def seccion(t):
    print(f"\n{Y}  ▸ {W}{t}{RS}")
    print(f"{Y}  {'─'*56}{RS}")

def ok(t):   print(f"  {G}✔  {W}{t}{RS}")
def info(t): print(f"  {B}ℹ  {D}{t}{RS}")
def warn(t): print(f"  {Y}⚠  {t}{RS}")

def pf(prompt, minv=None, maxv=None):
    while True:
        try:
            v = float(input(f"  {C}→ {W}{prompt}: {RS}"))
            if minv is not None and v < minv:
                print(f"  {Y}⚠  Mínimo: {minv}{RS}"); continue
            if maxv is not None and v > maxv:
                print(f"  {Y}⚠  Máximo: {maxv}{RS}"); continue
            return v
        except ValueError:
            print(f"  {R_}✖  Ingresa un número (usa punto decimal).{RS}")

def pi(prompt, rango):
    while True:
        try:
            v = int(input(f"  {C}→ {W}{prompt}: {RS}"))
            if v not in rango:
                print(f"  {R_}✖  Elige entre {min(rango)} y {max(rango)}.{RS}"); continue
            return v
        except ValueError:
            print(f"  {R_}✖  Ingresa un número entero.{RS}")

def semaforo(tj, tj_max):
    m = tj_max - tj
    if   m > 20: return G,  "✔ Seguro",   m
    elif m > 10: return Y,  "⚠ Normal",   m
    elif m >  0: return Y,  "⚠ Límite",   m
    else:        return R_, "✖ Peligro",  m

# ─────────────────────────────────────────────────────────────────────────────
# SENSORES REALES (Linux)
# ─────────────────────────────────────────────────────────────────────────────

def leer_cpu_real():
    """Lee temperatura actual del CPU desde /sys/class/thermal (Linux)."""
    zonas = sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp"))
    tipos = sorted(glob.glob("/sys/class/thermal/thermal_zone*/type"))
    if not zonas:
        return None, {}
    temps = {}
    for z, t in zip(zonas, tipos):
        try:
            with open(t) as f: tipo = f.read().strip()
            with open(z) as f: val  = int(f.read().strip()) / 1000.0
            temps[tipo] = val
        except Exception:
            pass
    # Prioridad: sensor del paquete CPU
    for clave in ["x86_pkg_temp", "coretemp", "cpu-thermal", "k10temp"]:
        for k, v in temps.items():
            if clave in k.lower():
                return v, temps
    if temps:
        return max(temps.values()), temps
    return None, {}

# ─────────────────────────────────────────────────────────────────────────────
# TEMPERATURA DEL CUARTO
# ─────────────────────────────────────────────────────────────────────────────

def obtener_t_cuarto():
    seccion("TEMPERATURA DEL CUARTO")

    t_cpu_real, sensores = leer_cpu_real()
    if t_cpu_real:
        print(f"\n  {G}Sensores detectados en tu equipo:{RS}")
        for k, v in sensores.items():
            print(f"    {D}{k:<30} {v:.1f} °C{RS}")
        print()
        info(f"CPU en este momento: {t_cpu_real:.1f} °C  ← temperatura REAL del chip")
        info("El cuarto siempre está más fresco que el chip.")
        info(f"Estimación del cuarto basada en sensor: ~{t_cpu_real - 7:.0f} °C (CPU reposo − 7°C)")

    print(f"\n  {Y}¿En qué región estás?{RS}")
    print(f"  {D}  1. Costa Caribe (Magangué, Cartagena, Barranquilla...)")
    print(f"     2. Interior frío (Bogotá, Pasto, Manizales)")
    print(f"     3. Interior cálido (Cali, Bucaramanga, Cúcuta)")
    print(f"     4. Ingresar temperatura manualmente{RS}")
    reg = pi("Opción", range(1, 5))
    t_base = {1: 32.0, 2: 17.0, 3: 28.0, 4: 0.0}[reg]

    if reg == 4:
        return pf("Temperatura del cuarto [°C]", 5, 55)

    nombres = {1: "Costa Caribe", 2: "Interior frío", 3: "Interior cálido"}
    info(f"Base exterior {nombres[reg]}: ~{t_base:.0f} °C")
    t = t_base

    print(f"\n  {Y}¿Hora del día?{RS}")
    print(f"  {D}  1. Madrugada (−4°C)  2. Mañana (0°C)  3. Tarde (+4°C)  4. Noche (+1°C){RS}")
    t += {1: -4.0, 2: 0.0, 3: +4.0, 4: +1.0}[pi("Opción", range(1, 5))]

    print(f"\n  {Y}¿Climatización del cuarto?{RS}")
    print(f"  {D}  1. Aire acondicionado (−10°C)  2. Ventilador (−3°C)")
    print(f"     3. Ventanas abiertas (−1°C)     4. Cerrado sin ventilación (+3°C)")
    print(f"     5. Cuarto cerrado y pequeño (+6°C){RS}")
    t += {1: -10.0, 2: -3.0, 3: -1.0, 4: +3.0, 5: +6.0}[pi("Opción", range(1, 6))]
    t = round(t, 1)

    if t_cpu_real:
        t_desde_sensor = round(t_cpu_real - 7.0, 1)
        diff = abs(t - t_desde_sensor)
        if diff > 8:
            warn(f"Tu sensor sugiere ~{t_desde_sensor}°C. Si el cuarto tiene A/C puede ser correcto.")

    print(f"\n  {C}  Temperatura estimada del cuarto: {Y}{t} °C{RS}")
    corr = input(f"  {C}→ {W}¿Correcto? (s / escribe el valor real): {RS}").strip().lower()
    if corr not in ("s", ""):
        try: t = float(corr); ok(f"Ajustado a {t} °C")
        except ValueError: pass
    return t

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO PORTÁTIL
# ─────────────────────────────────────────────────────────────────────────────

def modulo_laptop():
    # ── Selección de CPU ──
    seccion("PROCESADOR DEL PORTÁTIL")
    print(f"\n  {Y}{'Nº':<4} {'Procesador':<32} {'TDP_base':>9} {'TDP_boost':>10} {'Tj_max':>7}{RS}")
    print(f"  {'─'*66}")
    for k, (n, tb, tbst, tj, rjc, rs) in CPUS_LAPTOP.items():
        print(f"  {D}{k:<4}{RS} {n:<32} {C}{tb:>7}W{RS}  {Y}{tbst:>7}W{RS}  {M}{tj:>5}°C{RS}")
    op = str(pi("Número de tu procesador", range(1, 19)))
    n, tdp_b, tdp_bst, tj_max, r_jc, r_sis_fab = CPUS_LAPTOP[op]
    if op == "18":
        n        = input(f"  {C}→ {W}Nombre: {RS}")
        tdp_b    = pf("TDP base [W]", 1, 300)
        tdp_bst  = pf("TDP boost [W]", tdp_b, 400)
        tj_max   = pf("Tj_max [°C]", 60, 120)
        r_jc     = pf("R_jc [°C/W]", 0.01, 2)
        r_sis_fab= pf("R_sistema de fábrica [°C/W]", 0.01, 5)
    ok(f"{n}  |  TDP {tdp_b}–{tdp_bst} W  |  Tj_max = {tj_max} °C")

    # ── Pasta actual ──
    seccion("PASTA TÉRMICA ACTUAL")
    print(f"\n  {D}La pasta llena los microsurcos entre el chip y el heat pipe.")
    print(f"  Su resistencia térmica determina cuánto calor puede pasar.{RS}\n")
    print(f"  {Y}{'Nº':<4} {'Pasta':<44} {'R [°C/W]':>10}{RS}")
    print(f"  {'─'*60}")
    for k, (pn, pr, pk) in PASTAS.items():
        print(f"  {D}{k:<4}{RS} {pn:<44} {C}{pr:>9.3f}{RS}")
    op_p = str(pi("Número", range(1, 9)))
    pasta_n, r_pasta, _ = PASTAS[op_p]
    if op_p == "8": r_pasta = pf("R_pasta real [°C/W]", 0.01, 10)
    ok(f"{pasta_n}  →  R_pasta = {r_pasta} °C/W")

    # ── Estado actual del sistema de disipación ──
    seccion("ESTADO ACTUAL DEL SISTEMA DE DISIPACIÓN")
    print(f"\n  {D}Describe el estado del sistema de refrigeración integrado del portátil:{RS}\n")
    print(f"  {Y}{'Nº':<4} {'Sistema':<52} {'R_sis':>7}{RS}")
    print(f"  {'─'*66}")
    for k, (sn, rval, sdesc) in SISTEMAS_LAPTOP.items():
        print(f"  {D}{k:<4}{RS} {sn:<52} {C}{rval:>6.3f}{RS}")
        print(f"       {D}{sdesc}{RS}")
    op_s = str(pi("Número", range(1, 7)))
    sis_n, r_sis, _ = SISTEMAS_LAPTOP[op_s]
    if op_s == "6": r_sis = pf("R_sistema [°C/W]", 0.01, 5)
    ok(f"Sistema: {sis_n}  →  R_sis = {r_sis} °C/W")

    # ── Temperatura del cuarto ──
    t_cuarto = obtener_t_cuarto()

    # ── Superficie de uso ──
    seccion("SUPERFICIE DE USO")
    print(f"\n  {D}La superficie afecta la temperatura del aire que entra al portátil.{RS}\n")
    print(f"  {Y}{'Nº':<4} {'Superficie':<42} {'ΔT entrada':>11}{RS}")
    print(f"  {'─'*60}")
    for k, (sn, sdt) in SUPERFICIES.items():
        col = G if sdt <= 0 else (Y if sdt <= 10 else R_)
        print(f"  {D}{k:<4}{RS} {sn:<42} {col}{'+' if sdt>=0 else ''}{sdt:>3} °C{RS}")
    op_sf = str(pi("Número", range(1, 7)))
    sup_n, dt_sup = SUPERFICIES[op_sf]
    ok(f"{sup_n}  →  ΔT_entrada = {'+' if dt_sup>=0 else ''}{dt_sup} °C")

    # ── Carga de trabajo ──
    seccion("¿QUÉ TAREA ESTÁ REALIZANDO?")
    Q_op = {1: float(tdp_b),
            2: tdp_b + (tdp_bst - tdp_b)*0.40,
            3: tdp_b + (tdp_bst - tdp_b)*0.75,
            4: float(tdp_bst)}
    print(f"\n  {D}  1. Videos / navegar / ofimática              Q ≈ {Q_op[1]:.0f} W  (TDP base)")
    print(f"     2. Clases virtuales / multitarea             Q ≈ {Q_op[2]:.0f} W")
    print(f"     3. Edición / compilación / juegos medios     Q ≈ {Q_op[3]:.0f} W")
    print(f"     4. Render / juegos exigentes / estrés total  Q ≈ {Q_op[4]:.0f} W  (TDP boost){RS}")
    Q = Q_op[pi("Opción", range(1, 5))]

    # ── GPU dedicada ──────────────────────────────────────────────────────────
    seccion("¿EL PORTÁTIL TIENE GPU DEDICADA?")
    print(f"\n  {D}Una GPU discreta genera calor adicional que eleva la temperatura")
    print(f"  del chasis y afecta la capacidad de enfriamiento del CPU.{RS}\n")
    print(f"  {Y}  1. No, solo gráficos integrados (iGPU)")
    print(f"     2. Sí, tiene GPU dedicada (NVIDIA / AMD / Intel Arc){RS}\n")
    tiene_gpu = pi("Opción", range(1, 3)) == 2

    Q_gpu = 0.0
    gpu_n = "—"
    T_j_gpu = None

    if tiene_gpu:
        print(f"\n  {Y}{'Nº':<5} {'GPU':<40} {'TDP_base':>9} {'TDP_max':>9} {'Tj_max':>8}{RS}")
        print(f"  {'─'*74}")
        for k, (gn, gtb, gtbst, gtj, _) in GPUS_LAPTOP.items():
            print(f"  {D}{k:<5}{RS} {gn:<40} {C}{gtb:>7}W{RS}  {Y}{gtbst:>7}W{RS}  {M}{gtj:>6}°C{RS}")
        op_g = str(pi("Número de tu GPU", range(1, 13)))
        gpu_n, gpu_tdp_b, gpu_tdp_bst, gpu_tj_max, gpu_rjc = GPUS_LAPTOP[op_g]
        if op_g == "12":
            gpu_n      = input(f"  {C}→ {W}Nombre GPU: {RS}")
            gpu_tdp_b  = pf("TDP base GPU [W]", 1, 300)
            gpu_tdp_bst= pf("TDP máx GPU [W]", gpu_tdp_b, 400)
            gpu_tj_max = pf("Tj_max GPU [°C]", 60, 120)
            gpu_rjc    = pf("R_jc GPU [°C/W]", 0.01, 2)
        ok(f"{gpu_n}  |  TDP {gpu_tdp_b}–{gpu_tdp_bst} W  |  Tj_max = {gpu_tj_max} °C")

        print(f"\n  {Y}¿Qué hace la GPU en este escenario?{RS}")
        Q_gpu_op = {1: float(gpu_tdp_b),
                    2: gpu_tdp_b + (gpu_tdp_bst - gpu_tdp_b)*0.40,
                    3: gpu_tdp_b + (gpu_tdp_bst - gpu_tdp_b)*0.75,
                    4: float(gpu_tdp_bst)}
        print(f"  {D}  1. Solo video / 2D / reposo                Q_GPU ≈ {Q_gpu_op[1]:.0f} W")
        print(f"     2. Juego ligero / edición video             Q_GPU ≈ {Q_gpu_op[2]:.0f} W")
        print(f"     3. Juego medio / render moderado            Q_GPU ≈ {Q_gpu_op[3]:.0f} W")
        print(f"     4. Juego exigente / render completo (máx)   Q_GPU ≈ {Q_gpu_op[4]:.0f} W{RS}")
        Q_gpu = Q_gpu_op[pi("Carga GPU", range(1, 5))]

        # Temperatura de juntura GPU (modelo simplificado: comparte sistema de disipación)
        # La GPU agrega calor que sube T_entrada efectiva del CPU ~2-5 °C según potencia
        dt_gpu_efecto = round(Q_gpu * 0.04, 1)   # ~4% de Q_gpu en °C de penalización térmica cruzada
        T_j_gpu = round((t_cuarto + dt_sup) + Q_gpu * (gpu_rjc + r_sis * 1.1), 1)
        ok(f"Q_GPU = {Q_gpu:.0f} W  |  Efecto térmico cruzado sobre CPU: +{dt_gpu_efecto:.1f} °C")
    else:
        dt_gpu_efecto = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # CÁLCULOS
    # ─────────────────────────────────────────────────────────────────────────
    T_entrada = t_cuarto + dt_sup + dt_gpu_efecto
    R_total   = r_jc + r_pasta + r_sis
    T_j       = T_entrada + Q * R_total
    margen    = tj_max - T_j
    col_j, est_j, _ = semaforo(T_j, tj_max)

    # ── Capacidad de disipación requerida ──────────────────────────────────
    # Despejando R_sis de la fórmula T_j = T_entrada + Q*(R_jc + R_pasta + R_sis)
    R_sis_max = (tj_max - T_entrada) / Q - r_jc - r_pasta
    R_sis_rec = R_sis_max * 0.80   # margen de seguridad 20%

    # Potencia máxima que puede disipar el sistema actual
    # Q_max = (Tj_max - T_entrada) / R_total
    Q_max_actual = (tj_max - T_entrada) / R_total if R_total > 0 else 0

    limpiar()
    titulo(f"ANÁLISIS TÉRMICO — {n.upper()}")

    # ── SECCIÓN A: Estado actual ──────────────────────────────────────────
    print(f"  {M}━━ A. ESTADO ACTUAL DEL SISTEMA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RS}\n")
    print(f"  {W}Procesador              : {C}{n}{RS}")
    print(f"  {W}GPU dedicada            : {C}{gpu_n}{RS}")
    print(f"  {W}Temperatura del cuarto  : {C}{t_cuarto:.1f} °C{RS}")
    print(f"  {W}Superficie de uso       : {C}{sup_n}  ({'+' if dt_sup>=0 else ''}{dt_sup} °C){RS}")
    if dt_gpu_efecto > 0:
        print(f"  {W}Efecto térmico GPU      : {Y}+{dt_gpu_efecto:.1f} °C{RS}  {D}(calor cruzado GPU→CPU){RS}")
    print(f"  {W}T° aire que entra       : {C}{T_entrada:.1f} °C{RS}  {D}(cuarto {t_cuarto:.1f} + sup {dt_sup:+.0f} + GPU {dt_gpu_efecto:+.1f}){RS}")
    print(f"  {W}Potencia disipada Q     : {C}{Q:.1f} W{RS}  {D}(calor que genera el CPU){RS}")
    print(f"  {W}Tj máxima del fabricante: {Y}{tj_max} °C{RS}\n")

    print(f"  {B}Modelo de resistencias térmicas (Ley de Fourier):{RS}")
    print(f"  {D}  T_j = T_entrada + Q × (R_jc + R_pasta + R_sistema){RS}\n")
    print(f"  {'Componente':<38} {'R [°C/W]':>10}  {'ΔT = Q×R':>10}")
    print(f"  {'─'*62}")
    for cn, cr in [("R juntura→cápsula   (R_jc)", r_jc),
                   (f"R pasta actual       (R_pasta)", r_pasta),
                   (f"R sistema disipación (R_sis)", r_sis)]:
        print(f"  {cn:<38} {M}{cr:>9.3f}{RS}   {D}{cr*Q:>8.1f} °C{RS}")
    print(f"  {'─'*62}")
    print(f"  {'R total':<38} {Y}{R_total:>9.3f}{RS}   {D}{R_total*Q:>8.1f} °C{RS}\n")

    print(f"  {Y}Temperatura de juntura T_j (estado actual):{RS}")
    print(f"    {col_j}T_j = {T_entrada:.1f} + {Q:.1f} × {R_total:.3f} = {T_j:.1f} °C{RS}")
    print(f"    {col_j}Estado: {est_j}  |  Margen: {margen:.1f} °C  (límite: {tj_max} °C){RS}\n")

    if   margen > 20: ok("Sistema actual maneja esta carga sin problemas.")
    elif margen > 10: warn("Sistema funcional pero el ventilador irá a máximas RPM.")
    elif margen >  0: print(f"  {Y}⚠  Throttling probable — el CPU se auto-limita para no quemarse.{RS}")
    else:             print(f"  {R_}✖  Sobrecalentamiento — supera el límite, riesgo de apagado.{RS}")

    # ── SECCIÓN B: Capacidad requerida ────────────────────────────────────
    print(f"\n  {M}━━ B. CAPACIDAD DE DISIPACIÓN REQUERIDA ━━━━━━━━━━━━━━━━━━━━━━{RS}\n")
    print(f"  {D}Despejando R_sis de la fórmula:")
    print(f"    R_sis_max = (Tj_max − T_entrada) / Q  −  R_jc  −  R_pasta{RS}\n")
    print(f"  {'Parámetro':<40} {'Valor':>12}")
    print(f"  {'─'*54}")
    print(f"  {'Tj_max (límite fabricante)':<40} {Y}{tj_max:>10.1f} °C{RS}")
    print(f"  {'T_entrada (aire al sistema)':<40} {C}{T_entrada:>10.1f} °C{RS}")
    print(f"  {'Q (calor a disipar)':<40} {C}{Q:>10.1f} W{RS}")
    print(f"  {'R_jc (fija, no modificable)':<40} {M}{r_jc:>10.3f} °C/W{RS}")
    print(f"  {'R_pasta (actual)':<40} {M}{r_pasta:>10.3f} °C/W{RS}")
    print(f"  {'─'*54}")
    if R_sis_max > 0:
        print(f"  {R_}{'R_sis MÁXIMA permitida':<40} {R_sis_max:>10.3f} °C/W{RS}")
        print(f"  {G}{'R_sis RECOMENDADA (con 20% margen)':<40} {R_sis_rec:>10.3f} °C/W{RS}")
        print(f"\n  {W}El sistema de disipación debe tener R_sis ≤ {R_}{R_sis_max:.3f} °C/W{RS}")
        print(f"  {W}Para operar con seguridad se recomienda R_sis ≤ {G}{R_sis_rec:.3f} °C/W{RS}")
    else:
        print(f"  {R_}No es posible disipar {Q:.0f} W con T_entrada = {T_entrada:.1f} °C")
        print(f"  sin sobrepasar Tj_max = {tj_max} °C usando solo R_jc + R_pasta.")
        print(f"  Es necesario reducir la carga, la temperatura de entrada, o mejorar la pasta.{RS}")

    print(f"\n  {Y}Potencia máxima que aguanta el sistema actual:{RS}")
    print(f"    {C}Q_max = (Tj_max − T_entrada) / R_total")
    print(f"          = ({tj_max} − {T_entrada:.1f}) / {R_total:.3f}")
    print(f"          = {Q_max_actual:.1f} W{RS}")
    if Q_max_actual < Q:
        print(f"    {R_}El sistema actual solo aguanta {Q_max_actual:.1f} W pero el CPU genera {Q:.1f} W → insuficiente{RS}")
    else:
        print(f"    {G}El sistema actual aguanta {Q_max_actual:.1f} W  ≥  {Q:.1f} W del CPU → suficiente{RS}")

    # ── SECCIÓN C: Comparativa de mejoras ────────────────────────────────
    print(f"\n  {M}━━ C. COMPARATIVA DE SOLUCIONES DE REFRIGERACIÓN ━━━━━━━━━━━━━{RS}\n")
    print(f"  {D}Cómo cambia la T_j y la R_sis_max con cada intervención:{RS}\n")

    soluciones = [
        ("Estado actual",                     r_pasta, r_sis,  dt_sup),
        ("Repaste con pasta fábrica nueva",    0.40,    r_sis,  dt_sup),
        ("Repaste con Arctic MX-4",            0.20,    r_sis,  dt_sup),
        ("Repaste con Thermal Grizzly",        0.12,    r_sis,  dt_sup),
        ("Base con ventiladores activos",      r_pasta, r_sis,  dt_sup - 6),
        ("Repaste MX-4 + base ventiladores",   0.20,    r_sis,  dt_sup - 6),
        ("Limpieza (reduce R_sis ~15%)",       r_pasta, r_sis*0.85, dt_sup),
        ("Repaste Grizzly + limpieza + base",  0.12,    r_sis*0.85, dt_sup - 6),
    ]

    print(f"  {'Solución':<38} {'R_pasta':>8} {'R_sis':>7} {'T_j':>8} {'Q_max':>8} {'Estado':>10}")
    print(f"  {'─'*84}")

    mejor = None
    mejor_qmax = -1

    for sol_n, rp, rs, dts in soluciones:
        Te_s = t_cuarto + dts
        Rt_s = r_jc + rp + rs
        Tj_s = Te_s + Q * Rt_s
        Qmx  = (tj_max - Te_s) / Rt_s if Rt_s > 0 else 0
        col_s, est_s, _ = semaforo(Tj_s, tj_max)
        marker = f" {C}◄{RS}" if sol_n == "Estado actual" else ""
        print(f"  {sol_n:<38} {M}{rp:>7.3f}{RS}  {M}{rs:>6.3f}{RS}  "
              f"{col_s}{Tj_s:>7.1f}°C{RS}  {G}{Qmx:>6.1f}W{RS}   {col_s}{est_s}{RS}{marker}")
        if Qmx > mejor_qmax and sol_n != "Estado actual":
            mejor_qmax = Qmx
            mejor = (sol_n, Tj_s, Qmx)

    # ── SECCIÓN D: Recomendación ──────────────────────────────────────────
    print(f"\n  {M}━━ D. RECOMENDACIÓN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RS}\n")
    if mejor:
        rec_n, rec_tj, rec_qmax = mejor
        print(f"  {G}► Mejor solución: {W}{rec_n}{RS}")
        print(f"    Con esta mejora el sistema puede disipar hasta {G}{rec_qmax:.1f} W{RS}")
        print(f"    y la T_j cae a {G}{rec_tj:.1f} °C{RS} (margen: {tj_max - rec_tj:.1f} °C)\n")

    if dt_sup >= 10:
        warn("La superficie actual bloquea la ventilación — usa mesa dura.")
    if t_cuarto >= 30:
        warn(f"Cuarto a {t_cuarto:.1f} °C — considera ventilador o aire acondicionado.")
    if r_pasta >= 0.40:
        warn("La pasta actual tiene alta resistencia — repaste con Arctic MX-4 o mejor.")
    ok("Mantén las rejillas de ventilación despejadas siempre.")

    # ── SECCIÓN E: Fórmulas para el informe ──────────────────────────────
    print(f"\n  {M}━━ E. FÓRMULAS APLICADAS (para incluir en el informe) ━━━━━━━━{RS}")
    print(f"  {D}")
    print(f"  Ley de Fourier (conducción — régimen estacionario):")
    print(f"    Q = ΔT / R_total      donde  R = d / (k × A)")
    print(f"")
    print(f"  Modelo de resistencias en serie:")
    print(f"    T_j = T_entrada + Q × (R_jc + R_pasta + R_sistema)")
    print(f"        = {T_entrada:.1f} + {Q:.1f} × ({r_jc:.3f} + {r_pasta:.3f} + {r_sis:.3f})")
    print(f"        = {T_j:.1f} °C")
    print(f"")
    print(f"  Capacidad de disipación requerida (despejando R_sis):")
    print(f"    R_sis_max = (Tj_max − T_entrada) / Q  −  R_jc  −  R_pasta")
    if R_sis_max > 0:
        print(f"              = ({tj_max} − {T_entrada:.1f}) / {Q:.1f}  −  {r_jc:.3f}  −  {r_pasta:.3f}")
        print(f"              = {R_sis_max:.3f} °C/W")
    print(f"")
    print(f"  Potencia máxima disipable por el sistema actual:")
    print(f"    Q_max = (Tj_max − T_entrada) / R_total")
    print(f"          = ({tj_max} − {T_entrada:.1f}) / {R_total:.3f}")
    print(f"          = {Q_max_actual:.1f} W")
    print(f"")
    print(f"  Energía disipada en 1 hora (Primera Ley de la Termodinámica):")
    print(f"    E = Q × t = {Q:.1f} W × 3600 s = {Q*3600/1000:.1f} kJ = {Q*3600/3.6e6:.4f} kWh{RS}\n")

    # ── SECCIÓN F: GPU dedicada ───────────────────────────────────────────
    if tiene_gpu and T_j_gpu is not None:
        print(f"  {M}━━ F. ANÁLISIS TÉRMICO — GPU DEDICADA ({gpu_n.upper()}) ━━━━━━━━━━━━{RS}\n")
        col_gpu, est_gpu, _ = semaforo(T_j_gpu, gpu_tj_max)
        margen_gpu = gpu_tj_max - T_j_gpu
        print(f"  {W}GPU                    : {C}{gpu_n}{RS}")
        print(f"  {W}Q_GPU                  : {C}{Q_gpu:.1f} W{RS}")
        print(f"  {W}R_jc GPU               : {M}{gpu_rjc:.3f} °C/W{RS}")
        print(f"  {W}T_j GPU estimada       : {col_gpu}{T_j_gpu:.1f} °C{RS}  {D}(límite: {gpu_tj_max} °C){RS}")
        print(f"  {W}Margen GPU             : {col_gpu}{margen_gpu:.1f} °C  |  Estado: {est_gpu}{RS}")
        print(f"  {W}Efecto térmico cruzado : {Y}+{dt_gpu_efecto:.1f} °C{RS}  {D}sobre T_entrada del CPU{RS}\n")
        info("El calor de la GPU eleva la temperatura del chasis, reduciendo la eficiencia")
        info("del sistema de disipación del CPU (efecto de calor cruzado).")
        print()

    # ── SECCIÓN G: Texto para el documento académico ─────────────────────
    print(f"  {M}━━ G. TEXTO PARA EL DOCUMENTO ACADÉMICO ━━━━━━━━━━━━━━━━━━━━━━━{RS}")
    print(f"  {D}Copia estas secciones directamente en tu trabajo colaborativo.{RS}\n")

    # Determinar estado verbal para el documento
    if   margen > 20: estado_txt = "opera dentro de rangos seguros"
    elif margen > 10: estado_txt = "opera cerca del límite de confort térmico"
    elif margen >  0: estado_txt = "presenta signos de throttling térmico"
    else:             estado_txt = "supera el límite térmico de seguridad"

    # Mejor solución del comparativo
    if mejor:
        rec_nombre, rec_tj2, rec_qmax2 = mejor
    else:
        rec_nombre, rec_tj2, rec_qmax2 = "mantenimiento preventivo", T_j, Q_max_actual

    Q_total = Q + Q_gpu

    linea = "─" * 66

    print(f"\n{Y}{'═'*68}{RS}")
    print(f"{Y}  DIAGNÓSTICO DE LA PROBLEMÁTICA (Análisis Termodinámico del{RS}")
    print(f"{Y}  Estado Actual){RS}")
    print(f"{Y}{'═'*68}{RS}\n")

    print(f"""  El sistema analizado corresponde a un portátil equipado con el
  procesador {n}, cuyo TDP base es de {tdp_b} W con picos de hasta
  {tdp_bst} W en modo boost, y temperatura de juntura máxima (Tj_max)
  de {tj_max} °C según especificaciones del fabricante. El equipo opera
  en la región de la Costa Caribe colombiana, donde la temperatura
  ambiente típica ronda los {t_cuarto:.1f} °C, condición que agrava el
  sobrecalentamiento al reducir el gradiente térmico disponible para
  la disipación de calor.

  Aplicando el modelo de resistencias térmicas en serie derivado de
  la Ley de Fourier, se tiene:

      T_j = T_entrada + Q × (R_jc + R_pasta + R_sistema)

  Donde T_entrada representa la temperatura del aire que ingresa al
  sistema de refrigeración, equivalente a {T_entrada:.1f} °C (temperatura
  del cuarto {t_cuarto:.1f} °C, corrección por superficie {dt_sup:+.0f} °C{
    f", efecto térmico GPU +{dt_gpu_efecto:.1f} °C" if dt_gpu_efecto > 0 else ""}). La
  resistencia total del sistema es R_total = {R_total:.3f} °C/W,
  compuesta por R_jc = {r_jc:.3f} °C/W (juntura a cápsula),
  R_pasta = {r_pasta:.3f} °C/W ({pasta_n}) y
  R_sistema = {r_sis:.3f} °C/W ({sis_n}).

  La temperatura de juntura estimada es:

      T_j = {T_entrada:.1f} + {Q:.1f} × {R_total:.3f} = {T_j:.1f} °C

  Este valor indica que el procesador {estado_txt}, con un margen de
  seguridad de {margen:.1f} °C respecto al límite del fabricante.
  El sistema actual puede disipar como máximo {Q_max_actual:.1f} W antes de
  superar Tj_max.""")

    if tiene_gpu:
        print(f"""
  Adicionalmente, el portátil cuenta con la GPU dedicada {gpu_n},
  que bajo la carga evaluada genera {Q_gpu:.1f} W adicionales. El calor
  producido por ambos componentes asciende a {Q_total:.1f} W en total,
  y el efecto de calor cruzado de la GPU eleva la temperatura de
  entrada efectiva al sistema de disipación del CPU en {dt_gpu_efecto:.1f} °C,
  agravando las condiciones térmicas del conjunto.""")

    print(f"""
  Las principales fuentes de ineficiencia identificadas son: las
  elevadas temperaturas ambientales de la región Caribe, el estado
  de la pasta térmica ({pasta_n}), el nivel de
  obstrucción del sistema de ventilación ({sis_n}),
  y la superficie de operación ({sup_n}).

  La energía térmica disipada en una hora de operación bajo esta
  carga equivale a:

      E = {Q:.1f} W × 3600 s = {Q*3600/1000:.1f} kJ  ({Q*3600/3.6e6:.4f} kWh)

  Este dato ilustra el flujo continuo de energía que el sistema debe
  gestionar, en concordancia con la Primera Ley de la Termodinámica,
  que establece la conservación de energía en todo proceso térmico.""")

    print(f"\n{Y}{'═'*68}{RS}")
    print(f"{Y}  DESCRIPCIÓN DETALLADA DE LA SOLUCIÓN PLANTEADA{RS}")
    print(f"{Y}{'═'*68}{RS}\n")

    print(f"""  Con base en el diagnóstico termodinámico realizado, se plantea
  una estrategia de mejora escalonada orientada a reducir la
  resistencia térmica total del sistema y aumentar la capacidad de
  disipación de calor del portátil.

  La solución recomendada por el análisis computacional es:
  "{rec_nombre}". Con esta intervención, la temperatura de
  juntura desciende a {rec_tj2:.1f} °C y el sistema logra disipar hasta
  {rec_qmax2:.1f} W, mejorando notablemente el margen de seguridad
  (Tj_max − T_j = {tj_max - rec_tj2:.1f} °C).

  Las acciones propuestas se fundamentan en los tres mecanismos de
  transferencia de calor de la termodinámica:

  1. Conducción: Se propone la aplicación de pasta térmica de alta
     conductividad (Arctic MX-4, k = 8,5 W/m·K, o Thermal Grizzly
     Kryonaut, k = 12,5 W/m·K) en sustitución de la pasta actual
     ({pasta_n}, R_pasta = {r_pasta:.3f} °C/W).
     Esto reduce la resistencia de la interfaz y mejora el flujo de
     calor por conducción desde la juntura hacia el disipador.

  2. Convección: La limpieza profunda del sistema de ventilación
     elimina el polvo acumulado que obstruye el paso del aire,
     reduciendo R_sistema aproximadamente un 15 % y aumentando la
     tasa de convección forzada. Complementariamente, el uso de una
     base activa con ventiladores externos reduce la temperatura de
     entrada al sistema en hasta 6 °C, ampliando el gradiente térmico
     disponible (ΔT = Tj_max − T_entrada) para la disipación.

  3. Equilibrio térmico y gestión del entorno: Se recomienda operar
     el equipo exclusivamente sobre superficies duras y planas (mesa
     de madera, vidrio o metal) que no obstruyan las rejillas de
     ventilación, y preferir horarios de uso en los que la temperatura
     del cuarto sea menor (madrugada o mañana). En entornos con
     temperatura superior a 30 °C, el uso de aire acondicionado o
     ventilación activa del cuarto se convierte en una medida de
     primer orden.""")

    if tiene_gpu:
        print(f"""
  Dado que el equipo incorpora la GPU {gpu_n}, se recomienda
  activar el perfil de rendimiento equilibrado (no máximo) durante
  tareas que no requieran toda la potencia gráfica, limitando así
  Q_GPU y el efecto de calor cruzado (+{dt_gpu_efecto:.1f} °C) sobre el CPU.
  En sesiones de alta carga gráfica, el uso combinado de base activa
  y pasta premium resulta imprescindible para mantener ambos
  componentes dentro de sus límites seguros de operación.""")

    print(f"""
  El cálculo de la capacidad requerida del sistema de disipación
  establece que R_sis debe ser ≤ {R_sis_max:.3f} °C/W (máximo) y,
  con un margen de seguridad del 20 %, se recomienda un sistema
  con R_sis ≤ {R_sis_rec:.3f} °C/W. La comparativa de soluciones
  muestra que la combinación de repaste con pasta premium, limpieza
  del ventilador y base activa es la intervención que maximiza la
  capacidad disipativa del sistema sin necesidad de modificaciones
  estructurales del hardware.""")

    print(f"\n{Y}{'═'*68}{RS}")
    print(f"{Y}  RESULTADOS ESPERADOS{RS}")
    print(f"{Y}{'═'*68}{RS}\n")

    print(f"""  La implementación de las soluciones propuestas permitirá obtener
  los siguientes resultados cuantificables y cualitativos:

  · Reducción de la temperatura de juntura del CPU de {T_j:.1f} °C a un
    valor estimado de {rec_tj2:.1f} °C, lo que representa una disminución
    de {T_j - rec_tj2:.1f} °C y un incremento del margen de seguridad de
    {margen:.1f} °C a {tj_max - rec_tj2:.1f} °C respecto al límite de {tj_max} °C.

  · Aumento de la potencia máxima disipable por el sistema de
    {Q_max_actual:.1f} W a {rec_qmax2:.1f} W, ampliando la capacidad operativa
    del equipo para tareas de mayor carga computacional sin riesgo
    de throttling térmico.

  · Eliminación o reducción significativa del throttling térmico
    automático que actualmente limita el rendimiento del procesador,
    lo que se traducirá en mayor fluidez en aplicaciones de edición,
    programación, videoconferencias y multitarea.

  · Mayor durabilidad de los componentes electrónicos, ya que operar
    de forma sostenida por debajo del 80 % de Tj_max reduce el estrés
    térmico y la degradación acelerada de los materiales internos.

  · Reducción de la energía eléctrica desperdiciada como calor no
    disipado, en línea con los principios de eficiencia energética
    establecidos por la Primera y Segunda Ley de la Termodinámica.

  · Mejora de la experiencia de uso en el contexto climático de
    Magangué, Bolívar, donde las altas temperaturas ambientales
    representan un factor de riesgo permanente para los equipos
    portátiles utilizados en actividades académicas y laborales.""")

    print(f"\n{Y}{'═'*68}{RS}")
    print(f"{Y}  CONCLUSIONES{RS}")
    print(f"{Y}{'═'*68}{RS}\n")

    print(f"""  El análisis termodinámico desarrollado mediante el software de
  cálculo de disipación térmica permitió cuantificar con precisión
  el comportamiento térmico del portátil equipado con el procesador
  {n} en las condiciones ambientales propias del municipio de
  Magangué, Bolívar.

  Se verificó que la temperatura de juntura estimada ({T_j:.1f} °C) se
  sitúa con un margen de {margen:.1f} °C respecto al límite del
  fabricante ({tj_max} °C), y que el sistema de disipación actual tiene
  una capacidad máxima de {Q_max_actual:.1f} W, cifra que debe interpretarse
  en relación con los picos de potencia del procesador ({tdp_bst} W en
  modo boost).

  La aplicación de la Ley de Fourier a través del modelo de
  resistencias térmicas en serie demostró que la temperatura de
  juntura depende de manera directa de tres variables controlables:
  la resistencia de la pasta térmica, el estado del sistema de
  ventilación y la temperatura del aire de entrada. Reducir
  cualquiera de estas variables produce mejoras mensurables en el
  equilibrio térmico del sistema.

  La Primera Ley de la Termodinámica confirma que la energía
  eléctrica consumida ({Q:.1f} W) se transforma íntegramente en calor
  que debe ser transferido al ambiente; dicha energía equivale a
  {Q*3600/1000:.1f} kJ por hora de operación. La Segunda Ley, por su parte,
  explica por qué este proceso es irreversible y por qué ninguna
  solución puede eliminar completamente la generación de calor,
  haciendo indispensable un sistema de disipación adecuado.

  La solución más eficiente identificada — {rec_nombre} —
  reduce T_j a {rec_tj2:.1f} °C y eleva la capacidad disipativa a
  {rec_qmax2:.1f} W, constituyendo una mejora técnicamente viable y de
  bajo costo que puede implementarse sin abrir o modificar el
  hardware de forma invasiva.

  En conclusión, la termodinámica proporciona las herramientas
  científicas necesarias para diagnosticar, modelar y resolver el
  problema del sobrecalentamiento en computadores portátiles,
  demostrando que la física aplicada tiene un impacto directo y
  medible en el rendimiento y la vida útil de los dispositivos
  tecnológicos usados cotidianamente.""")

    print(f"\n{G}{'═'*68}{RS}")
    print(f"{G}  Texto listo — cópialo en tu documento (Times New Roman 12, 1.5){RS}")
    print(f"{G}{'═'*68}{RS}\n")

    guardar = input(f"  {C}→ {W}¿Guardar reporte completo en .txt? (s/n): {RS}").strip().lower()
    if guardar == "s":
        nombre_arch = "reporte_termica_cpu.txt"
        with open(nombre_arch, "w", encoding="utf-8") as f:
            f.write("REPORTE ANÁLISIS TÉRMICO — PORTÁTIL\n")
            f.write("Universidad de Cartagena | Física I — Mecánica y Termodinámica\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Procesador              : {n}\n")
            f.write(f"GPU dedicada            : {gpu_n}\n")
            f.write(f"T° cuarto               : {t_cuarto:.1f} °C\n")
            f.write(f"Superficie de uso       : {sup_n} (ΔT={dt_sup:+}°C)\n")
            f.write(f"Efecto térmico GPU      : +{dt_gpu_efecto:.1f} °C\n" if dt_gpu_efecto > 0 else "")
            f.write(f"T° entrada al sistema   : {T_entrada:.1f} °C\n")
            f.write(f"Potencia CPU Q          : {Q:.1f} W\n")
            f.write(f"Potencia GPU Q_gpu      : {Q_gpu:.1f} W\n" if tiene_gpu else "")
            f.write(f"Potencia total          : {Q_total:.1f} W\n" if tiene_gpu else "")
            f.write(f"R_jc                    : {r_jc:.3f} °C/W\n")
            f.write(f"R_pasta ({pasta_n}) : {r_pasta:.3f} °C/W\n")
            f.write(f"R_sistema ({sis_n}) : {r_sis:.3f} °C/W\n")
            f.write(f"R_total                 : {R_total:.3f} °C/W\n")
            f.write(f"T_j estimada CPU        : {T_j:.1f} °C\n")
            f.write(f"T_j estimada GPU        : {T_j_gpu:.1f} °C\n" if T_j_gpu else "")
            f.write(f"Tj_max (fabricante)     : {tj_max} °C\n")
            f.write(f"Margen de seguridad     : {margen:.1f} °C\n\n")
            f.write(f"Capacidad requerida:\n")
            if R_sis_max > 0:
                f.write(f"  R_sis_max = {R_sis_max:.3f} °C/W\n")
                f.write(f"  R_sis_rec = {R_sis_rec:.3f} °C/W (con 20% margen)\n\n")
            f.write(f"Q_max del sistema actual: {Q_max_actual:.1f} W\n\n")
            f.write(f"Fórmulas:\n")
            f.write(f"  T_j = {T_entrada:.1f} + {Q:.1f} × {R_total:.3f} = {T_j:.1f} °C\n")
            if R_sis_max > 0:
                f.write(f"  R_sis_max = ({tj_max} - {T_entrada:.1f}) / {Q:.1f} - {r_jc:.3f} - {r_pasta:.3f} = {R_sis_max:.3f} °C/W\n")
            f.write(f"  E = {Q:.1f} × 3600 = {Q*3600/1000:.1f} kJ\n\n")
            f.write("=" * 60 + "\n")
            f.write("TEXTO PARA EL DOCUMENTO ACADÉMICO\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"[Las secciones de Diagnóstico, Solución, Resultados y\n")
            f.write(f" Conclusiones se generaron en pantalla. Cópialas desde\n")
            f.write(f" la terminal o vuelve a ejecutar el programa.]\n")
        ok(f"Guardado: {nombre_arch}")

# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO ESCRITORIO
# ─────────────────────────────────────────────────────────────────────────────

def modulo_desktop():
    seccion("PROCESADOR DE ESCRITORIO")
    print(f"\n  {Y}{'Nº':<4} {'Procesador':<32} {'TDP':>6} {'Tj_max':>7} {'R_jc':>8}{RS}")
    print(f"  {'─'*62}")
    for k, (n, tdp, tj, rjc) in CPUS_DESKTOP.items():
        print(f"  {D}{k:<4}{RS} {n:<32} {C}{tdp:>5}W{RS} {Y}{tj:>6}°C{RS} {M}{rjc:>6.3f}°C/W{RS}")
    op = str(pi("Número", range(1, 13)))
    n, tdp, tj_max, r_jc = CPUS_DESKTOP[op]
    if op == "12":
        n      = input(f"  {C}→ {W}Nombre: {RS}")
        tdp    = pf("TDP [W]", 1, 500)
        tj_max = pf("Tj_max [°C]", 60, 120)
        r_jc   = pf("R_jc [°C/W]", 0.01, 2)
    ok(f"{n}  |  TDP={tdp}W  |  Tj_max={tj_max}°C")

    seccion("PASTA TÉRMICA")
    print(f"\n  {Y}{'Nº':<4} {'Pasta':<44} {'R [°C/W]':>10}{RS}")
    print(f"  {'─'*60}")
    for k, (pn, pr, _) in PASTAS.items():
        print(f"  {D}{k:<4}{RS} {pn:<44} {C}{pr:>9.3f}{RS}")
    op_p = str(pi("Número", range(1, 9)))
    pasta_n, r_pasta, _ = PASTAS[op_p]
    if op_p == "8": r_pasta = pf("R_pasta [°C/W]", 0.01, 10)
    ok(f"{pasta_n}  →  R_pasta = {r_pasta} °C/W")

    t_cuarto = obtener_t_cuarto()

    seccion("¿QUÉ ESTARÁ HACIENDO EL PC?")
    print(f"\n  {D}  El PC consume energía directa de la red eléctrica (no batería).\n")
    print(f"  1. Ofimática / navegación / video         ~{tdp*0.25:.0f} W")
    print(f"  2. Multitarea / compilación ligera        ~{tdp*0.55:.0f} W")
    print(f"  3. Juegos / edición de video              ~{tdp*0.80:.0f} W")
    print(f"  4. Render 3D / estrés total (TDP máximo)  ~{tdp:.0f} W")
    print(f"  5. Consumo real medido con vatímetro{RS}")
    op_c = pi("Opción", range(1, 6))
    Qs = {1: tdp*0.25, 2: tdp*0.55, 3: tdp*0.80, 4: float(tdp)}
    Q  = Qs[op_c] if op_c != 5 else pf(f"Consumo [W]", 1, tdp*1.2)

    R_max    = (tj_max - t_cuarto) / Q
    R_dis_m  = R_max - r_jc - r_pasta
    R_dis_rec = R_dis_m * 0.80
    T_j_rec  = t_cuarto + Q * (r_jc + r_pasta + R_dis_rec)

    limpiar()
    titulo(f"ANÁLISIS TÉRMICO — {n.upper()}")

    print(f"  {M}━━ A. PARÁMETROS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RS}")
    print(f"  {W}Procesador     : {C}{n}{RS}")
    print(f"  {W}Pasta térmica  : {C}{pasta_n}{RS}")
    print(f"  {W}T° cuarto      : {C}{t_cuarto:.1f} °C{RS}")
    print(f"  {W}Potencia Q     : {C}{Q:.1f} W{RS}")
    print(f"  {W}Tj_max         : {Y}{tj_max} °C{RS}\n")

    print(f"  {M}━━ B. CAPACIDAD DE DISIPADOR REQUERIDA ━━━━━━━━━━━━━━━━━━━━━━━━{RS}")
    print(f"  {D}  T_j = T_cuarto + Q × (R_jc + R_pasta + R_dis)")
    print(f"  Despejando R_dis para T_j = Tj_max:{RS}\n")
    print(f"  {'Parámetro':<40} {'Valor':>12}")
    print(f"  {'─'*54}")
    print(f"  {'R_jc (juntura→cápsula)':<40} {M}{r_jc:>10.3f} °C/W{RS}")
    print(f"  {'R_pasta':<40} {M}{r_pasta:>10.3f} °C/W{RS}")
    if R_dis_m > 0:
        print(f"  {R_}{'R_dis MÁXIMA permitida':<40} {R_dis_m:>10.3f} °C/W{RS}")
        print(f"  {G}{'R_dis RECOMENDADA (margen 20%)':<40} {R_dis_rec:>10.3f} °C/W{RS}")
        print(f"\n  {G}Con R_dis recomendado: T_j = {T_j_rec:.1f} °C  (margen: {tj_max-T_j_rec:.1f} °C){RS}")
    else:
        print(f"  {R_}No hay disipador posible — reduce carga o temperatura del cuarto.{RS}")

    print(f"\n  {M}━━ C. EVALUACIÓN DE DISIPADORES DEL MERCADO ━━━━━━━━━━━━━━━━━━{RS}\n")
    print(f"  {'Disipador':<36} {'R':>6} {'T_j':>8} {'Margen':>8} {'Estado':>10}")
    print(f"  {'─'*72}")
    validos = []
    for nd, rd, tipo, _ in DISIPADORES_DESKTOP:
        Tj_d = t_cuarto + Q * (r_jc + r_pasta + rd)
        m_d  = tj_max - Tj_d
        col_d, est_d, _ = semaforo(Tj_d, tj_max)
        mk = f"{G}✔{RS}" if R_dis_m > 0 and rd <= R_dis_m else f"{R_}✖{RS}"
        if R_dis_m > 0 and rd <= R_dis_m: validos.append((nd, rd, tipo, Tj_d))
        print(f"  {mk} {nd:<34} {rd:>5.2f}  {col_d}{Tj_d:>7.1f}°C{RS}  {m_d:>7.1f}°C  {col_d}{est_d}{RS}  {D}[{tipo}]{RS}")

    print(f"\n  {M}━━ D. RECOMENDACIÓN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RS}\n")
    if validos:
        eco = min(validos, key=lambda x: x[1])
        opt = min(validos, key=lambda x: x[3])
        print(f"  {G}► Más económico válido : {W}{eco[0]}{RS}  (R={eco[1]:.2f} °C/W, {eco[2]})")
        if opt[0] != eco[0]:
            print(f"  {G}► Mejor rendimiento    : {W}{opt[0]}{RS}  (T_j = {opt[3]:.1f} °C)")
    else:
        warn("Ningún disipador listado es suficiente — considera undervolting o custom loop.")

    print(f"\n  {M}━━ E. FÓRMULAS (para el informe) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RS}")
    print(f"  {D}  T_j = T_cuarto + Q × (R_jc + R_pasta + R_dis)")
    print(f"  R_dis_max = (Tj_max − T_cuarto) / Q  −  R_jc  −  R_pasta")
    if R_dis_m > 0:
        print(f"            = ({tj_max} − {t_cuarto:.1f}) / {Q:.1f}  −  {r_jc:.3f}  −  {r_pasta:.3f}")
        print(f"            = {R_dis_m:.3f} °C/W")
    print(f"  E = Q × t = {Q:.1f} W × 3600 s = {Q*3600/1000:.0f} kJ{RS}\n")

# ─────────────────────────────────────────────────────────────────────────────

def main():
    limpiar()
    titulo("ANALIZADOR DE DISIPACIÓN TÉRMICA — CPU\n  Termodinámica Aplicada | Universidad de Cartagena\n  Física I — Mecánica y Termodinámica")
    print(f"  {D}Basado en la Ley de Fourier — modelo de resistencias en serie{RS}\n")
    print(f"  {Y}¿Qué equipo vas a analizar?{RS}")
    print(f"  {D}  1. Portátil / laptop")
    print(f"     2. Computadora de escritorio{RS}\n")
    tipo = pi("Tipo de equipo", range(1, 3))
    if tipo == 1: modulo_laptop()
    else:         modulo_desktop()
    print(f"\n  {G}¡Listo! Datos listos para el informe.{RS}\n")

if __name__ == "__main__":
    main()
