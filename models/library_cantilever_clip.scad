/*
Experiment 004: cantilever clip based on Simple Snap-Fit Joints Library 0.36.

Original library and example by Fausto Petraccone (fpetrac):
https://www.thingiverse.com/thing:1860118
Licensed CC Attribution-NonCommercial.
*/

include <../docs/snapfit-know-hows/simple-snapfit-joints-lib/files/SnapLib.0.36.scad>

$fn = 64;

part_id = 0; // 0 = print layout, 1 = clip, 2 = insert, 3 = assembly preview

insert_radius = 3.3;
insert_height = insert_radius * 1.5;
arm_length = 5;
hook_height = 3;
part_width = 8;
fit_scale = 0.99;
insert_web = 1.2;

module library_clip() {
    difference() {
        union() {
            linear_extrude(height = part_width)
                polygon([
                    [0, -hook_height],
                    [-11, -hook_height],
                    [-11, insert_height + hook_height],
                    [0, insert_height + hook_height]
                ]);

            SnapY(l = arm_length, h = hook_height, a = 35, b = part_width);

            translate([0, insert_height, 0])
                mirror([0, 1, 0])
                    SnapY(l = arm_length, h = hook_height, a = 35, b = part_width);
        }

        translate([0, insert_height / 2, -0.1])
            cylinder(h = part_width + 0.2, r = insert_radius);
    }
}

module matching_insert() {
    scaled_height = fit_scale * insert_height;
    scaled_length = fit_scale * arm_length;

    union() {
        difference() {
            cube([scaled_length, scaled_height, part_width]);
            translate([0, scaled_height / 2, -0.1])
                cylinder(h = part_width + 0.2, r = insert_radius);
        }

        // The author's visual test gauge is split into two crescents. This web
        // joins them inside the clip's empty cable cavity without changing the
        // exterior surface that contacts the snap arms.
        cube([scaled_length, scaled_height, insert_web]);
    }
}

module print_layout() {
    library_clip();
    translate([12, 0, 0]) matching_insert();
}

module assembly_preview() {
    color("gold") library_clip();
    color("deepskyblue", 0.75)
        matching_insert();
}

if (part_id == 1) {
    library_clip();
} else if (part_id == 2) {
    matching_insert();
} else if (part_id == 3) {
    assembly_preview();
} else {
    print_layout();
}
