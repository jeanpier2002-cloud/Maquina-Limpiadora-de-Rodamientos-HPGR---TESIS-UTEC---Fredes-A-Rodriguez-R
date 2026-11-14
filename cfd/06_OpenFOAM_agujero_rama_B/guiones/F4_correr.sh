#!/bin/bash
# F4 - corre un caso ya construido, en paralelo con 4 rangos, y resume
source /usr/lib/openfoam/openfoam2606/etc/bashrc
C=$HOME/cfd01/F4/$1
cd "$C" || exit 1
foamDictionary system/controlDict -entry writeFormat -set binary >/dev/null 2>&1
foamDictionary system/controlDict -entry writeInterval -set 0.0175 >/dev/null 2>&1
foamDictionary system/decomposeParDict -entry numberOfSubdomains -set 4 >/dev/null 2>&1
rm -rf processor* ; decomposePar -force > log.decomposePar 2>&1
t0=$(date +%s)
mpirun --oversubscribe -np 4 kinematicParcelFoam -parallel > log.par 2>&1
rc=$?; t1=$(date +%s)
echo "=================================================================="
echo "$1   exit=$rc   pared=$((t1-t0)) s   ExecutionTime=$(grep ExecutionTime log.par | tail -1 | awk '{print $3}') s"
grep -ciE "FOAM FATAL" log.par | sed 's/^/  FOAM FATAL: /'
echo "--- masa suspendida frente al tiempo ---"
paste <(grep -oE "^Time = [0-9.e-]+" log.par | awk '{print $3}') <(grep "Current mass in system" log.par | awk '{print $6}') | awk 'NR%100==0 {printf "  t=%-9s m=%s\n", $1, $2}'
echo "--- balance final por patch ---"
awk '/^Cloud: kinematicCloud$/{buf=""} {buf=buf"\n"$0} END{print buf}' log.par | grep -E "Current number of parcels|Current mass in system|mass introduced|Parcel fate|escape" | head -24
reconstructPar -latestTime > log.reconstructPar 2>&1
du -sh "$C" | awk '{print "  disco: "$1}'
