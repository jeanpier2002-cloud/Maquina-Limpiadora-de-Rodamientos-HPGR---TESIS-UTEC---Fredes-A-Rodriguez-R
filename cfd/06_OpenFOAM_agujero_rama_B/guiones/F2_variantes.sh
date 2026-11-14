#!/bin/bash
# =============================================================================
#  F2 - Crea las variantes del piloto a partir de base/
#
#  V1_ico_absorbe  icoUncoupledKinematicParcelFoam, aire congelado, placa absorbe
#                  (es a la vez S0 -huella y alcance- y S1 con deposicion perfecta)
#  V2_aco_absorbe  kinematicParcelFoam, aire acoplado (RAS kEpsilon), placa absorbe
#  V3_ico_adhiere  aire congelado, placa stick  (la gota se pega y sigue en la nube)
#  V4_ico_rebota   aire congelado, placa rebound (e=0,3 mu=0,2)
#  V5_ico_RR       aire congelado, placa absorbe, diametros Rosin-Rammler en masa
#
#  PASO DE TIEMPO: 5e-5 s en TODAS las variantes.
#  Razon medida, no supuesta: con 2e-4 s el caso acoplado diverge en el primer paso
#  (errores de continuidad ~1e18) porque el aire arrastrado en la celda de inyeccion
#  se acelera hacia 27 m/s y el Courant del aire llega a 1,35 con celdas de 4 mm.
#  Con 5e-5 s, Co(aire) ~ 0,34 a 27 m/s. Se usa el mismo dt en las cinco variantes
#  para que la comparacion sea a igualdad de todo lo demas.
# =============================================================================
source /usr/lib/openfoam/openfoam2606/etc/bashrc

BASE="$HOME/cfd01/F2_piloto"
TAB="/mnt/c/Users/Usuario/AppData/Local/Temp/claude/G--Mi-unidad-Semestre-X-TESIS-II-Sistema-de-aspersi-n-CFD01-OPENFOAM/217d7132-3a5c-4cff-aaed-21d01264a2f8/scratchpad/tablas"

RHO_LIQ=982.1203530851709
MASS_TOTAL=0.00746220369     # = 0,149244074 kg/s x 0,05 s  (lo calcula gen_abanico.py)
DURACION=0.05
DT=5e-05
ENDTIME=0.05
# floor(300 entradas x 5e-5 s x 22000) = 330 >= 300  ->  TODAS las entradas de la
# tabla disparan en cada paso. Es imprescindible: con menos de 300 parcels por paso
# el modelo (injectorI = parcelI*N/nParcels, aritmetica entera) dispararia SIEMPRE
# el mismo subconjunto de entradas y el resto del abanico no existiria nunca.
PPS=22000

# ---------------------------------------------------------------------------
nube () {
  local caso="$1" acoplado="$2" tipo="$3" e="$4" mu="$5"
  cat > "$caso/constant/kinematicCloudProperties" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object kinematicCloudProperties; }

solution
{
    active          true;
    coupled         $acoplado;
    transient       yes;
    cellValueSourceCorrection no;
    maxCo           0.3;              // el rastreo de parcels se subdivide solo

    sourceTerms { schemes { U semiImplicit 1; } }
    // 'mu' lo pide la nube con colisiones (ico), 'muc' la nube simple (acoplada)
    interpolationSchemes { rho cell; U cellPoint; mu cell; muc cell; }
    integrationSchemes   { U Euler; }
}

constantProperties
{
    rho0            $RHO_LIQ;         // agua a 62 C (la tabla lo repite por entrada)
}

subModels
{
    particleForces
    {
        sphereDrag;
        gravity;
    }

    injectionModels
    {
        abanico
        {
            type             kinematicLookupTableInjection;
            inputFile        "parcelInjectionProperties";
            duration         $DURACION;
            parcelsPerSecond $PPS;
            randomise        false;   // OJO: con true la posicion sale de una entrada
                                      // al azar pero U y d de otra (en el fuente,
                                      // setProperties ignora randomise)
            massTotal        $MASS_TOTAL;
            parcelBasisType  mass;
            SOI              0;
        }
    }

    dispersionModel none;

    patchInteractionModel localInteraction;

    localInteractionCoeffs
    {
        patches
        (
            placa   { type $tipo; e $e; mu $mu; }
            fondo   { type rebound; e 0.3; mu 0.2; }
            abierto { type escape; }
        );
    }

    stochasticCollisionModel none;

    // icoUncoupledKinematicParcelFoam construye una nube CON colisiones
    // (basicKinematicCollidingCloud) y exige esta entrada; no la usamos
    collisionModel none;

    surfaceFilmModel none;
}

cloudFunctions
{
    // masa acumulada por CARA de patch: mapa de deposicion en la resolucion de la malla
    campos_de_impacto
    {
        type        patchInteractionFields;
        resetMode   none;
    }

    // lista de CADA parcel que golpea la placa: permite construir el mapa a
    // cualquier resolucion, independiente de la malla, y cerrar el balance de masa
    impactos
    {
        type              particlePostProcessing;
        maxStoredParcels  5000000;
        patches           (placa);
        fields            (position U d nParticle rho age origId);
    }
}
DICT
}

# ---------------------------------------------------------------------------
crear () {
  local nombre="$1" solver="$2" acoplado="$3" tipo="$4" e="$5" mu="$6" tabla="$7" turb="$8"
  local caso="$BASE/$nombre"
  rm -rf "$caso"
  cp -r "$BASE/base" "$caso"
  rm -f "$caso"/log.blockMesh "$caso"/log.checkMesh
  cp -r "$caso/0.orig" "$caso/0"
  cp "$TAB/$tabla/parcelInjectionProperties" "$caso/constant/parcelInjectionProperties"
  nube "$caso" "$acoplado" "$tipo" "$e" "$mu"
  foamDictionary "$caso/system/controlDict" -entry application   -set "$solver"  > /dev/null
  foamDictionary "$caso/system/controlDict" -entry deltaT        -set "$DT"      > /dev/null
  foamDictionary "$caso/system/controlDict" -entry endTime       -set "$ENDTIME" > /dev/null
  foamDictionary "$caso/system/controlDict" -entry writeInterval -set 0.01       > /dev/null
  cat > "$caso/constant/turbulenceProperties" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object turbulenceProperties; }

simulationType  $turb;
$( [ "$turb" = "RAS" ] && echo "RAS { RASModel kEpsilon; turbulence on; printCoeffs on; }" )
DICT
  printf "  %-16s %-32s coupled=%-4s placa=%-8s tabla=%-5s turb=%s\n" \
         "$nombre" "$solver" "$acoplado" "$tipo" "$tabla" "$turb"
}

echo "creando variantes en $BASE   (dt=$DT s, endTime=$ENDTIME s, pps=$PPS)"
crear V1_ico_absorbe icoUncoupledKinematicParcelFoam no  escape  1   0    fijo laminar
crear V2_aco_absorbe kinematicParcelFoam             yes escape  1   0    fijo RAS
crear V3_ico_adhiere icoUncoupledKinematicParcelFoam no  stick   1   0    fijo laminar
crear V4_ico_rebota  icoUncoupledKinematicParcelFoam no  rebound 0.3 0.2  fijo laminar
crear V5_ico_RR      icoUncoupledKinematicParcelFoam no  escape  1   0    RR   laminar

echo
n=$(grep -c "^    (" "$BASE/V1_ico_absorbe/constant/parcelInjectionProperties")
echo "entradas de la tabla        : $n"
echo "parcels por paso            : $(python3 -c "print(int($n*$DT*$PPS))")   (tiene que ser >= $n)"
echo "parcels por segundo         : $(python3 -c "print(int($n*$PPS))")"
echo "pasos de la corrida         : $(python3 -c "print(int($ENDTIME/$DT))")"
echo "Courant del aire a 27 m/s   : $(python3 -c "print(round(27*$DT/0.004,3))")"
