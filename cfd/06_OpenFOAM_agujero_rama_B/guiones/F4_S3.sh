#!/bin/bash
# F4/S3 - sensibilidades sobre S2 (malla de 16 mm ya generada, se reutiliza)
# Cada variante cambia UN parametro y nada mas.
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SP=/mnt/c/Users/Usuario/AppData/Local/Temp/claude/G--Mi-unidad-Semestre-X-TESIS-II-Sistema-de-aspersi-n-CFD01-OPENFOAM/217d7132-3a5c-4cff-aaed-21d01264a2f8/scratchpad
B=$HOME/cfd01/F4

for v in "$@"; do
  C=$B/S3_$v
  rm -rf "$C"; mkdir -p "$C"
  cp -r $B/S2_seis/system $B/S2_seis/0.orig "$C/"
  mkdir -p "$C/constant"
  cp $B/S2_seis/constant/{g,transportProperties,turbulenceProperties,kinematicCloudProperties} "$C/constant/"
  cp -r $B/S2_seis/constant/polyMesh "$C/constant/"
  cp -r $B/S2_seis/constant/triSurface "$C/constant/" 2>/dev/null
  cp -r "$C/0.orig" "$C/0"
  if [ "$v" = "rebote" ]; then
    cp $B/S2_seis/constant/tabla_* "$C/constant/"
    sed -i 's|pared_agujero       { type escape; }|pared_agujero       { type rebound; e 0.3; mu 0.2; }|' \
        "$C/constant/kinematicCloudProperties"
  else
    cp "$SP/tablas_S3/$v"/tabla_* "$C/constant/"
  fi
  n=$(cat "$C"/constant/tabla_* | grep -c "^    (")
  echo "  S3_$v : $(grep -m1 -c . /dev/null); entradas=$n ; pared=$(grep -m1 'pared_agujero ' "$C/constant/kinematicCloudProperties" | sed 's/.*type //;s/;.*//')"
done
