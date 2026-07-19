/*
Experiment 003: calculated cantilever latch.

This model uses the cantilever snap relation used in the snap-fit design
guide and the reference OpenSCAD library:

  h = 1.09 * eps * l^2 / y

where:
  h   = root thickness for a tapered cantilever arm
  eps = allowed strain as an absolute value
  l   = free arm length
  y   = required deflection / undercut

Part selector:
  part_id = 0; // preview
  part_id = 1; // latch with flexible cantilever hook
  part_id = 2; // striker block with ramp and catch window
*/

$fn = 48;

part_id = 0;

// Material/design assumptions for a conservative PLA/PETG first print.
allowed_strain = 0.018; // about 60% of 0.03 for repeated assembly tests
arm_length = 26;
target_deflection = 3.4;
safety_factor = 1.35;

arm_root_thickness = 1.09 * allowed_strain * arm_length * arm_length / target_deflection / safety_factor;
arm_tip_thickness = arm_root_thickness * 0.55;
arm_width = 8;
clearance = 0.45;

base_thickness = 3;
handle_length = 20;
handle_width = 18;
hook_height = target_deflection - clearance;
hook_length = 4.2;
root_relief = 1.2;

striker_length = 32;
striker_width = 16;
striker_height = base_thickness + target_deflection + arm_tip_thickness + 1.2;

module rounded_plate(size, r = 1.0) {
    hull() {
        for (x = [r, size[0] - r])
        for (y = [r, size[1] - r])
            translate([x, y, 0]) cylinder(h = size[2], r = r);
    }
}

module tapered_arm(length, width, root_h, tip_h) {
    hull() {
        translate([0, 0, 0])
            cube([0.2, width, root_h]);
        translate([length - 0.2, 0, 0])
            cube([0.2, width, tip_h]);
    }
}

module latch() {
    rounded_plate([handle_length, handle_width, base_thickness], 1.2);

    // Root pad and relief bump reduce abrupt stress concentration at the arm.
    translate([handle_length - 0.4, handle_width / 2 - arm_width / 2 - 1.2, base_thickness])
        cube([2.2, arm_width + 2.4, arm_root_thickness]);

    translate([handle_length - 0.4, handle_width / 2 - arm_width / 2, base_thickness])
        tapered_arm(arm_length, arm_width, arm_root_thickness, arm_tip_thickness);

    translate([handle_length + arm_length - hook_length, handle_width / 2 - arm_width / 2, base_thickness + arm_tip_thickness - 0.1])
        cube([hook_length, arm_width, hook_height + 0.1]);

    // Small underside clearance marker: this face should not collide with the striker base.
    translate([handle_length + 4, handle_width / 2 - 0.4, base_thickness - 0.05])
        cube([arm_length - 8, 0.8, 0.1]);
}

module striker_void() {
    channel_w = arm_width + 2 * clearance;
    channel_h = target_deflection + arm_root_thickness + clearance;

    // Open insertion tunnel for the arm.
    translate([-0.1, striker_width / 2 - channel_w / 2, base_thickness - 0.1])
        cube([striker_length + 0.2, channel_w, channel_h]);

    // Entry ramp clearance.
    translate([-0.1, striker_width / 2 - channel_w / 2, base_thickness + arm_tip_thickness])
        rotate([0, -24, 0])
            cube([9, channel_w, target_deflection + 1.0]);

    // Catch/release window after the hook passes the ramp.
    translate([striker_length - 10, striker_width / 2 - channel_w / 2 - 0.1, base_thickness + arm_tip_thickness])
        cube([6.5, channel_w + 0.2, hook_height + clearance + 0.8]);
}

module striker() {
    difference() {
        cube([striker_length, striker_width, striker_height]);
        striker_void();
    }
}

module both_preview() {
    latch();
    translate([64, 1, 0]) striker();
}

if (part_id == 1) {
    latch();
} else if (part_id == 2) {
    striker();
} else {
    both_preview();
}

