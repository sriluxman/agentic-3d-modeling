/*
Small sliding-clearance coupon based on JointSCAD's dovetail profile.
Upstream: https://github.com/HopefulLlama/JointSCAD
Pinned source commit: 447888065b30721267db6011faeaf8e4e95ee5ff
License: MIT
*/

use <../components/vendor/jointscad/DovetailJoint.scad>

$fn = 32;
part_id = 0; // 0 = print plate, 1 = receiver rack, 2 = key, 3 = assembly preview

clearances = [0.15, 0.25, 0.35]; // Per-side XY clearance in mm.
joint_dimensions = [10, 5, 6];
receiver_dimensions = [10, 8, 6];
receiver_gap = 2;
cut_epsilon = 0.2;

module clearance_cutout(clearance) {
    profile_width = joint_dimensions[0] / 2;
    scale_x = (profile_width + 2 * clearance) / profile_width;
    scale_y = (joint_dimensions[1] + 2 * clearance) / joint_dimensions[1];
    center_x = joint_dimensions[0] / 2;
    center_y = joint_dimensions[1] / 2;

    translate([center_x, center_y, -cut_epsilon])
        scale([scale_x, scale_y, 1])
            translate([-center_x, -center_y, 0])
                dovetailJointA([
                    joint_dimensions[0],
                    joint_dimensions[1],
                    joint_dimensions[2] + 2 * cut_epsilon
                ], 1);
}

module receiver(clearance, marker_count) {
    difference() {
        cube(receiver_dimensions);

        translate([0, (receiver_dimensions[1] - joint_dimensions[1]) / 2, 0])
            clearance_cutout(clearance);

        // Dimples identify the clearance after the rack leaves the print bed.
        for (marker = [0 : marker_count - 1])
            translate([
                receiver_dimensions[0] / 2 + (marker - (marker_count - 1) / 2) * 1.8,
                0.9,
                receiver_dimensions[2] - 0.5
            ])
                cylinder(h = 0.7, r = 0.55);
    }
}

module receiver_rack() {
    for (index = [0 : len(clearances) - 1])
        translate([index * (receiver_dimensions[0] + receiver_gap), 0, 0])
            receiver(clearances[index], index + 1);

    // Rear bridges keep the receivers indexed without closing either channel end.
    for (index = [0 : len(clearances) - 2])
        translate([
            (index + 1) * receiver_dimensions[0] + index * receiver_gap,
            receiver_dimensions[1] - 2,
            0
        ])
            cube([receiver_gap, 2, 2]);
}

module dovetail_key() {
    difference() {
        union() {
            dovetailJointA(joint_dimensions, 1);
            translate([1, -1, joint_dimensions[2]])
                cube([8, 7, 2]);
        }

        // Finger hole in the stop/handle.
        translate([joint_dimensions[0] / 2, joint_dimensions[1] / 2, joint_dimensions[2] - 0.1])
            cylinder(h = 2.2, r = 1.2);
    }
}

module print_plate() {
    receiver_rack();
    translate([12, 13, 0]) dovetail_key();
}

module assembly_preview() {
    color("gold") receiver_rack();
    color("deepskyblue", 0.75)
        translate([
            receiver_dimensions[0] + receiver_gap,
            (receiver_dimensions[1] - joint_dimensions[1]) / 2,
            3
        ])
            dovetail_key();
}

if (part_id == 1) {
    receiver_rack();
} else if (part_id == 2) {
    dovetail_key();
} else if (part_id == 3) {
    assembly_preview();
} else {
    print_plate();
}
