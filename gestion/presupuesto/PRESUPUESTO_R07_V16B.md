# Presupuesto completo de la máquina, R07 V16B (02/11/2026)

**Estado.** Cálculo EJECUTADO; enfoque económico de **HPGR D-077** (confirmado). Es una **estimación de clase 4**: orden de magnitud con ingeniería básica, exactitud típica de −30 % / +50 %.
- **Precios:** de referencia, con fuente o [HIPÓTESIS]. Sin IGV.
- **Se reemplaza con las cotizaciones del usuario** cuando lleguen (pedidas el 02/11; P1-28, D1 del plan).

**Responde a** la observación 3.8 del asesor a la P2: «Presupuesto: Incluye fabricación, cabina, tanque, filtro y tablero». La P2 solo costeó los componentes comerciales: S/ 33 855 (cap. IX, tabla de costos).

**Archivos:**
- metrado: `scripts/c1_metrado_cad.py` (freecadcmd, CAD V16B) → `resultados/METRADO_CAD_V16B.json`, con 706 piezas;
- cálculo: `scripts/c1_presupuesto.py` → `resultados/PRESUPUESTO_R07_V16B.json`;
- tabla para la tesis: `05_ENTREGABLES_TESIS/insumos_P3/tabla_presupuesto_completo.tex`.

## 1. Método

| Tipo | Cómo se costea | Fuente |
|---|---|---|
| **Piezas fabricadas** | Masa del CAD × precio del material, más horas de taller × tarifa. Horas por complejidad [HIPÓTESIS]: estructura 0,15 h/kg; soldado con mecanizado 0,40; centradores con ajustes 0,60; chapa inox 0,25; tubería inox 0,35 | Masas: CAD V16B. Material: base de precios de la P2 (A36 a US$ 3,16/kg; inox a US$ 5,62/kg, los máximos de los rangos) |
| **Tarifa de taller** | **S/ 50,5/h** | Soldador homologado en Lima a S/ 3 500/mes (aviso de 2026, cazvid.com) ÷ 208 h × 1,5 de cargas sociales × 2,0 de gastos generales y utilidad [HIPÓTESIS] |
| **Comerciales** | Precio publicado por fabricante o distribuidor. Lo importado lleva × 1,20 [HIPÓTESIS: flete, seguro, agente y ad valorem] | Ver el JSON (`precios`): Siemens CPU 1214C (Steiner Electric), KTP700 (Bürklin), ATV320 (Standard Electric Supply), FTL31 (RS), DDA (Hellopro), carcasa de filtro inox de 2" (Grainger) y la base de la P2 |
| **Sin precio publicado** | [HIPÓTESIS] con rango | Por ejemplo, CRN 15-3 (Lenntech: «a pedido»), SF47, ROBA-slip, SPKVS 200K y Rittal AE |
| Tipo de cambio | US$ = S/ 3,448 (SUNAT, 13/10/2026); € = S/ 3,91 (P2) | — |
| **Rango de cada partida** | Con fuente: 0,85–1,20. HIPÓTESIS: 0,70–1,50 | — |
| Ingeniería de fabricación y gestión | 5 % [HIPÓTESIS] | — |
| Contingencia | 15 % | La misma de la P2 |

## 2. Resultado

| Partida | Base (S/) | Rango (S/) |
|---|---:|---:|
| A. Mesa, centrado y traslado (bastidor, apoyos, centradores, ruedas, rieles, 24 pedestales con anclajes, traslado D-071) | 58 713 | 41 711–86 846 |
| B. Aspersión y accionamiento (rotor 316L, boquillas, unión rotativa, SF47, ROBA, transmisión, soporte superior y cartucho) | 34 795 | 24 896–51 118 |
| C. Hidráulica y filtrado (CRN 15-3, filtro ES2, colador, válvulas, tubería fija, instrumentos) | 40 100 | 29 441–57 407 |
| D. Tanques y calentamiento (tanque de 600 L, tanque de enjuague, aislamiento, 3 × 12 kW, sensores, dosificadoras, insumos iniciales) | 32 778 | 25 190–44 675 |
| E. Cabina hermética (53,8 m² de paneles inox, puerta de guillotina y su motor, extractor, luminarias, sellos) | 42 856 | 30 759–62 763 |
| F. Drenaje (Hidrostal A02Q-S, desviadora, IBC) | 5 689 | 3 983–8 534 |
| G. Tablero eléctrico y control (Rittal, S7-1200, KTP700, 2 variadores, aparamenta, cableado) | 26 364 | 20 014–36 429 |
| H. Obra civil, montaje y puesta en marcha | 20 615 | 14 430–30 922 |
| **Subtotal** | **261 910** | |
| Ingeniería de fabricación y gestión (5 %) | 13 096 | |
| Contingencia (15 %) | 41 251 | |
| **Total sin IGV** | **≈ S/ 316 000 (≈ US$ 92 000)** | **245 000–433 000** |
| IGV (18 %), aparte | 56 926 | |

**Cómo se reparte:**
- Con fuente publicada: solo el 18 % del subtotal. El resto es [HIPÓTESIS] o mixto (material con fuente y horas supuestas).
- Fabricación: S/ 95 837, de los cuales S/ 41 359 son mano de obra de taller.

**Pareto.** Las 10 partidas más grandes suman la mitad del subtotal. Son las que más importan para las cotizaciones:

| Partida | S/ | Estado |
|---|---:|---|
| Paneles de inox 304 de la cabina (768 kg) | 24 572 | material con fuente; espesor de 1,5 mm y horas [HIPÓTESIS] |
| 24 pedestales del riel en inox 304 (656 kg; D-073) | 21 012 | ídem |
| Bomba CRN 15-3 en 316 | 17 388 | [HIPÓTESIS]: CR 10-06 × 1,4 |
| Soporte superior, cartucho, alojamientos y ménsula (682 kg A36) | 12 625 | CAD; el cartucho de R04 pesa 128 kg y es candidato a simplificarse |
| Montaje y puesta en marcha (2 técnicos × 15 días) | 12 115 | [HIPÓTESIS] |
| Dosificadoras Grundfos DDA (2) | 10 127 | con fuente |
| Filtro de bolsa inox | 9 138 | con fuente (Grainger) |
| Obra civil | 8 500 | [HIPÓTESIS] |
| Ruedas SPKVS 200K (4) | 7 448 | [HIPÓTESIS]. La P2 valoró otro producto (LE-ALST, US$ 220) |
| Traslado D-071 | 6 885 | mixto (D-071 §5) |

## 3. Hallazgo: la evaluación económica de la P2 cambia

**La fórmula de la P2:** VAN = −I + A·n·f·C_m, con A = 3,791 (5 años, 10 %) y C_m = S/ 885 de mano de obra manual por rodamiento. La fracción de equilibrio es f* = I/(A·n·C_m).

| Rodamientos por año | f* con la P2 (I = S/ 33 855) | f* con el presupuesto completo (I ≈ S/ 316 000) |
|---|---:|---:|
| 4 | 252 % | 2 357 % |
| 12 | 84 % | 786 % |
| 24 | 42 % | 393 % |
| 48 | 21 % | 196 % |

**Lectura:**
- **Con el presupuesto completo, el ahorro de mano de obra no recupera la inversión en 5 años** con ningún volumen razonable. Haría falta reemplazar más del 100 % de la limpieza manual.
- **La P2 subestimaba la inversión ~9 veces**, porque excluía justo lo que pide el asesor.

**Decisión (HPGR D-077, usuario, 02/11: «Beneficio requerido (Recomendado)»):** la tesis no presenta un VAN solo con la mano de obra. Presenta:
- la inversión de clase 4 con su rango;
- el **beneficio por rodamiento necesario** para recuperarla en 5 años al 10 %: B* = I/(A·n);
- la comparación de B* con lo que se conoce de cada rodamiento: mano de obra (S/ 885), solvente, residuos peligrosos y parada de la prensa HPGR. Estos tres últimos son [DATO EXTERNO: la empresa de remanufactura o el cliente].

| Rodamientos por año | B* base (S/) | Rango (S/) | Mano de obra manual hoy (S/) |
|---|---:|---:|---:|
| 4 | 20 857 | 16 142–28 559 | 885 |
| 12 | 6 952 | 5 381–9 520 | 885 |
| 24 | 3 476 | 2 690–4 760 | 885 |
| 48 | 1 738 | 1 345–2 380 | 885 |

**Lectura:** la mano de obra cubre entre el 4 % y el 51 % de B*, según el volumen. El resto tendría que venir del solvente, los residuos, la seguridad y, sobre todo, del tiempo de parada de la prensa, que se debe cuantificar con el cliente. Tabla para la tesis: `05_ENTREGABLES_TESIS/insumos_P3/tabla_beneficio_requerido.tex`.

**Opciones que se evaluaron:**
1. **Medir el beneficio completo,** no solo la mano de obra:
   - solvente (10 L por rodamiento);
   - residuos peligrosos (75 kg);
   - seguridad;
   - tiempo de reacondicionamiento y disponibilidad de la prensa HPGR.

   Hacen falta esos datos [DATO EXTERNO: la empresa de remanufactura o el cliente]. Mientras tanto se puede informar el **beneficio por rodamiento que haría falta**: B* = I/(A·n), es decir, S/ 6 950 con 12 rodamientos al año o S/ 3 475 con 24.
2. **Ingeniería de valor** antes de cotizar:
   - simplificar el cartucho de R04;
   - dosificación más simple;
   - revisar el inox en los pedestales y en la cabina, que fueron decisiones (D-073 y D-057), y su efecto en la corrosión;
   - el ahorro posible es del orden del 10–20 %.
3. **Presentarlo tal cual:** inversión de clase 4 con su rango y la justificación técnica de la máquina, que es calidad, seguridad y medio ambiente, sin afirmar un retorno por mano de obra.

## 4. Limitaciones y abiertos

- **[HIPÓTESIS]** horas por kg, tarifa, factor de importación, espesor de los paneles, montaje, obra civil y todos los ítems sin precio publicado.
- **[VERIFICAR]**
  - los precios de A36 e inox se tomaron de los máximos internacionales de la P2. El A36 local probablemente es más barato;
  - el filtro de Grainger es un precio de lista.
- **[DATO EXTERNO PENDIENTE]** cotizaciones en Lima (pedidas): la estimación las reemplaza partida por partida, empezando por el Pareto del §2.
- **No incluye:** el rodamiento, el galpón, el puente grúa, la acometida eléctrica, ni el IGV en el total.
