// geo file for meshing with Gmsh meshing software created by FreeCAD

// enable multi-core processing
General.NumThreads = 20;

// open brep geometry
Merge "Cuerpo_A_Geometry.brep";

// group data
Physical Line("Edge1") = {1};
Physical Line("Edge10") = {10};
Physical Line("Edge11") = {11};
Physical Line("Edge12") = {12};
Physical Line("Edge13") = {13};
Physical Line("Edge14") = {14};
Physical Line("Edge15") = {15};
Physical Line("Edge16") = {16};
Physical Line("Edge17") = {17};
Physical Line("Edge18") = {18};
Physical Line("Edge19") = {19};
Physical Line("Edge2") = {2};
Physical Line("Edge20") = {20};
Physical Line("Edge21") = {21};
Physical Line("Edge22") = {22};
Physical Line("Edge23") = {23};
Physical Line("Edge24") = {24};
Physical Line("Edge25") = {25};
Physical Line("Edge26") = {26};
Physical Line("Edge27") = {27};
Physical Line("Edge28") = {28};
Physical Line("Edge29") = {29};
Physical Line("Edge3") = {3};
Physical Line("Edge30") = {30};
Physical Line("Edge31") = {31};
Physical Line("Edge32") = {32};
Physical Line("Edge33") = {33};
Physical Line("Edge34") = {34};
Physical Line("Edge35") = {35};
Physical Line("Edge36") = {36};
Physical Line("Edge37") = {37};
Physical Line("Edge38") = {38};
Physical Line("Edge39") = {39};
Physical Line("Edge4") = {4};
Physical Line("Edge40") = {40};
Physical Line("Edge41") = {41};
Physical Line("Edge42") = {42};
Physical Line("Edge43") = {43};
Physical Line("Edge44") = {44};
Physical Line("Edge45") = {45};
Physical Line("Edge46") = {46};
Physical Line("Edge47") = {47};
Physical Line("Edge48") = {48};
Physical Line("Edge49") = {49};
Physical Line("Edge5") = {5};
Physical Line("Edge50") = {50};
Physical Line("Edge51") = {51};
Physical Line("Edge52") = {52};
Physical Line("Edge53") = {53};
Physical Line("Edge54") = {54};
Physical Line("Edge55") = {55};
Physical Line("Edge56") = {56};
Physical Line("Edge57") = {57};
Physical Line("Edge6") = {6};
Physical Line("Edge7") = {7};
Physical Line("Edge8") = {8};
Physical Line("Edge9") = {9};
Physical Surface("Face1") = {1};
Physical Surface("Face10") = {10};
Physical Surface("Face11") = {11};
Physical Surface("Face12") = {12};
Physical Surface("Face13") = {13};
Physical Surface("Face14") = {14};
Physical Surface("Face15") = {15};
Physical Surface("Face16") = {16};
Physical Surface("Face17") = {17};
Physical Surface("Face18") = {18};
Physical Surface("Face19") = {19};
Physical Surface("Face2") = {2};
Physical Surface("Face20") = {20};
Physical Surface("Face21") = {21};
Physical Surface("Face3") = {3};
Physical Surface("Face4") = {4};
Physical Surface("Face5") = {5};
Physical Surface("Face6") = {6};
Physical Surface("Face7") = {7};
Physical Surface("Face8") = {8};
Physical Surface("Face9") = {9};
Physical Volume("Solid1") = {1};

// Characteristic Length
// Characteristic Length according CharacteristicLengthMap
// Edge8
Characteristic Length { 7 } = 2.5;
// Edge9
Characteristic Length { 8 } = 2.5;
// Edge13
Characteristic Length { 11 } = 2.5;
// Edge14
Characteristic Length { 12 } = 2.5;
// Edge27
Characteristic Length { 25 } = 2.5;
// Edge28
Characteristic Length { 26 } = 2.5;
// Edge38
Characteristic Length { 33 } = 2.5;
// Edge39
Characteristic Length { 34 } = 2.5;

// no boundary layer settings for this mesh
// min, max Characteristic Length
Mesh.CharacteristicLengthMax = 12.0;
Mesh.CharacteristicLengthMin = 2.5;
Mesh.MeshSizeFromCurvature = 12; // number of elements per 2*pi radians, 0 to deactivate

// optimize the mesh
Mesh.Optimize = 1;
Mesh.OptimizeNetgen = 0;
// High-order meshes optimization (0=none, 1=optimization, 2=elastic+optimization, 3=elastic, 4=fast curving)
Mesh.HighOrderOptimize = 0;

// mesh order
Mesh.ElementOrder = 1;

// mesh algorithm, only a few algorithms are usable with 3D boundary layer generation
// 2D mesh algorithm (1=MeshAdapt, 2=Automatic, 5=Delaunay, 6=Frontal, 7=BAMG, 8=DelQuad, 9=Packing Parallelograms, 11=Quasi-structured Quad)
Mesh.Algorithm = 2;
// 3D mesh algorithm (1=Delaunay, 2=New Delaunay, 4=Frontal, 7=MMG3D, 9=R-tree, 10=HTX)
Mesh.Algorithm3D = 1;

// subdivision algorithm
Mesh.SubdivisionAlgorithm = 0;

// incomplete second order elements
Mesh.SecondOrderIncomplete = 0;

// meshing
Geometry.Tolerance = 1e-06; // set geometrical tolerance (also used for merging nodes)
Mesh  3;
Coherence Mesh; // Remove duplicate vertices

// save
// For each group save not only the elements but the nodes too.;
Mesh.SaveGroupsOfNodes = 1;
// Needed for Group meshing too, because for one material there is no group defined;
// Ignore Physical definitions and save all elements;
Mesh.SaveAll = 1;
Save "Cuerpo_A_Mesh.unv";


// **********************************************************************
// Gmsh documentation:
// https://gmsh.info/doc/texinfo/gmsh.html#Mesh
//
// We do not check if something went wrong, like negative jacobians etc. You can run Gmsh manually yourself: 
//
// to see full Gmsh log, run in bash:
// C:\Program Files\FreeCAD 1.1\bin\gmsh.exe - C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R06\R06.1_centradores\resultados\k2m_v57\fem_contacto_v573\U1_SP_H12_b\gmsh_A\shape2mesh.geo
//
// to run Gmsh and keep file in Gmsh GUI (with log), run in bash:
// C:\Program Files\FreeCAD 1.1\bin\gmsh.exe C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R06\R06.1_centradores\resultados\k2m_v57\fem_contacto_v573\U1_SP_H12_b\gmsh_A\shape2mesh.geo
