mode = 0; // 0 = print layout, 1 = closed, 2 = partially open, 3 = body inspection

body_path = "../exports/skadis/skadis_sliding_box/box_body.stl";
lid_print_path = "../exports/skadis/skadis_sliding_box/sliding_lid.stl";
lid_assembly_path = "../exports/skadis/skadis_sliding_box/sliding_lid_assembly.stl";

module body() {
    color("gold") import(body_path);
}

module lid(y_position) {
    color("deepskyblue", 0.8)
        translate([2.25, y_position, 37.15])
            import(lid_assembly_path);
}

if (mode == 3) {
    body();
} else if (mode == 1) {
    body();
    lid(2.15);
} else if (mode == 2) {
    body();
    lid(27);
} else {
    body();
    translate([82, 0, 0])
        color("deepskyblue") import(lid_print_path);
}
