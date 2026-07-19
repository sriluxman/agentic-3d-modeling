/*
Two-part parametric snap-fit coupon for FDM testing.

Usage from OpenSCAD GUI:
  part_id = 0; // preview arrangement
  part_id = 1; // export the flexible tab side
  part_id = 2; // export the receiver side

Usage from CLI:
  openscad -o exports/plug.stl   -D part_id=1 models/snapfit_pair.scad
  openscad -o exports/socket.stl -D part_id=2 models/snapfit_pair.scad
*/

$fn = 48;

part_id = 0;

clearance = 0.45;
beam_width = 10;
beam_thickness = 2.2;
beam_length = 30;
hook_height = 0.6;
hook_length = 4.5;
base_thickness = 3;
wall = 2.4;
socket_length = 28;
socket_entry_chamfer = 2;
labels_enabled = false;

module label(txt, size = 4) {
    linear_extrude(height = 0.45)
        text(txt, size = size, halign = "center", valign = "center");
}

module rounded_plate(size, r = 1.2) {
    hull() {
        for (x = [r, size[0] - r])
        for (y = [r, size[1] - r])
            translate([x, y, 0]) cylinder(h = size[2], r = r);
    }
}

module plug() {
    plate_x = 24;
    plate_y = 22;

    rounded_plate([plate_x, plate_y, base_thickness], 1.4);

    // The beam starts at the front edge of the handle so only the free tongue
    // enters the socket. The handle stays outside and prevents base collision.
    translate([plate_x - 0.2, plate_y / 2 - beam_width / 2, base_thickness]) {
        cube([beam_length, beam_width, beam_thickness]);

        translate([beam_length - hook_length, 0, beam_thickness - 0.15])
            cube([hook_length, beam_width, hook_height + 0.15]);
    }

    if (labels_enabled) {
        translate([24, plate_y / 2, base_thickness - 0.05])
            label(str("plug C", clearance), 3.4);
    }
}

module socket_cutout(inner_w, inner_h) {
    translate([-0.1, wall, base_thickness - 0.1])
        cube([socket_length + 0.2, inner_w, inner_h + 0.2]);

    translate([-0.1, wall - 0.1, base_thickness + inner_h - hook_height - clearance])
        cube([socket_entry_chamfer, inner_w + 0.2, hook_height + clearance + 0.4]);
}

module socket_window(inner_w, inner_h) {
    translate([socket_length - 8, wall - 0.1, base_thickness + inner_h - hook_height - 0.2])
        cube([5.5, inner_w + 0.2, hook_height + clearance + 0.5]);
}

module socket() {
    inner_w = beam_width + 2 * clearance;
    inner_h = beam_thickness + hook_height + 1.1 * clearance;
    outer_w = inner_w + 2 * wall;
    outer_h = base_thickness + inner_h + wall;
    plate_x = 44;
    plate_y = outer_w + 8;

    translate([9, plate_y / 2 - outer_w / 2, 0]) {
        difference() {
            cube([socket_length, outer_w, outer_h]);
            socket_cutout(inner_w, inner_h);
            socket_window(inner_w, inner_h);
        }
    }

    if (labels_enabled) {
        translate([22, plate_y / 2, base_thickness - 0.05])
            label(str("socket C", clearance), 3.1);
    }
}

module both_preview() {
    plug();
    translate([64, 0, 0]) socket();
}

if (part_id == 1) {
    plug();
} else if (part_id == 2) {
    socket();
} else {
    both_preview();
}
