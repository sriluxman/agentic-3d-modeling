use <../components/vendor/jointscad/DovetailJoint.scad>

$fn = 32;
part_id = 0; // 0 plate, 1 India, 2 Austria, 3 assembled, 4 exploded, 5 collision, 10-15 color volumes

cube_size = 36;
half_width = cube_size / 2;
band_height = cube_size / 3;

dovetail_dimensions = [10, 5, 34.5];
dovetail_clearance = 0.25;
dovetail_top_gap = cube_size - dovetail_dimensions[2];
receiver_top = cube_size - dovetail_top_gap + dovetail_clearance;
eps = 0.05;

india_saffron = "#FF8C1A";
india_green = "#138808";
austria_red = "#C8102E";

module dovetail_key() {
    translate([-dovetail_dimensions[0] / 4 - eps, cube_size / 2 - dovetail_dimensions[1] / 2, 0])
        dovetailJointA(dovetail_dimensions, 1);
}

module dovetail_receiver_cut() {
    profile_width = dovetail_dimensions[0] / 2;
    scale_x = (profile_width + 2 * dovetail_clearance) / profile_width;
    scale_y = (dovetail_dimensions[1] + 2 * dovetail_clearance) / dovetail_dimensions[1];
    center_x = dovetail_dimensions[0] / 2;
    center_y = dovetail_dimensions[1] / 2;

    translate([-dovetail_dimensions[0] / 4, cube_size / 2 - dovetail_dimensions[1] / 2, 0])
        translate([center_x, center_y, -eps])
            scale([scale_x, scale_y, 1])
                translate([-center_x, -center_y, 0])
                    dovetailJointA([
                        dovetail_dimensions[0],
                        dovetail_dimensions[1],
                        receiver_top + 2 * eps
                    ], 1);
}

module india_core() {
    union() {
        translate([-half_width, 0, 0]) cube([half_width, cube_size, cube_size]);
        dovetail_key();
    }
}

module austria_core() {
    difference() {
        cube([half_width, cube_size, cube_size]);
        dovetail_receiver_cut();
    }
}

module india_band(index) {
    intersection() {
        india_core();
        translate([-half_width - 1, -1, index * band_height])
            cube([half_width + 7, cube_size + 2, band_height]);
    }
}

module austria_band(index) {
    intersection() {
        austria_core();
        translate([-1, -1, index * band_height])
            cube([half_width + 2, cube_size + 2, band_height]);
    }
}

module india_colored() {
    color(india_green) render(convexity=10) india_band(0);
    color("white") render(convexity=10) india_band(1);
    color(india_saffron) render(convexity=10) india_band(2);
}

module austria_colored() {
    color(austria_red) render(convexity=10) austria_band(0);
    color("white") render(convexity=10) austria_band(1);
    color(austria_red) render(convexity=10) austria_band(2);
}

module print_layout() {
    translate([-8, 0, 0]) india_colored();
    translate([8, 0, 0]) austria_colored();
}

module assembly() {
    india_colored();
    austria_colored();
}

module exploded() {
    translate([-7, 0, 0]) india_colored();
    translate([7, 0, 0]) austria_colored();
}

if (part_id == 1) {
    india_core();
} else if (part_id == 2) {
    austria_core();
} else if (part_id == 3) {
    assembly();
} else if (part_id == 4) {
    exploded();
} else if (part_id == 5) {
    intersection() {
        india_core();
        austria_core();
    }
} else if (part_id >= 10 && part_id <= 12) {
    translate([-8, 0, 0]) india_band(part_id - 10);
} else if (part_id >= 13 && part_id <= 15) {
    translate([8, 0, 0]) austria_band(part_id - 13);
} else {
    print_layout();
}
