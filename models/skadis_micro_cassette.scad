include <BOSL2/std.scad>
include <BOSL2/hinges.scad>
include <BOSL2/joiners.scad>
use <jointscad/DovetailJoint.scad>

$fn = 48;
part_id = 0; // 0 plate, 1 body, 2 lid, 3 divider, 4 latch, 5 closed, 6 open, 7 coupon
label = "SRI";

case_width = 70;
case_height = 36;
case_depth = 12;
wall = 1.6;
back_wall = 1.6;
corner_radius = 3;
lid_thickness = 1.6;
assembly_gap = 0.25;
open_angle = 95;

hinge_length = 50;
hinge_segments = 7;
hinge_offset = 3;
hinge_gap = 0.25;
hinge_diameter = 4;
hinge_hole = 2.2;
hinge_axis_y = case_height;
hinge_axis_z = case_depth + hinge_diameter / 2;
hinge_native_axis_y = assembly_gap;
hinge_native_axis_z = hinge_offset;

latch_length = 3.5;
latch_width = 5;
latch_snap = 0.1;
latch_thickness = 0.8;
latch_depth = 4;
latch_clearance = 0.25;
latch_boss_width = 10;
latch_boss_height = 4.2;

divider_thickness = 1.2;
divider_joint = [6, 4, back_wall + 0.2];
divider_joint_y = [12, 24];

seat_path = "../exports/components/skadis_clip_seat_rotated.stl";
seat_x = [-20, 20];
seat_y = case_height / 2;
seat_cut_radius = 13.8;

eps = 0.05;

module rounded_prism(width, height, depth, radius) {
    translate([0, height / 2, 0])
        linear_extrude(depth)
            offset(r=radius)
                square([width - 2 * radius, height - 2 * radius], center=true);
}

module hinge_half(inner=false) {
    knuckle_hinge(
        length=hinge_length,
        segs=hinge_segments,
        offset=hinge_offset,
        inner=inner,
        arm_angle=90,
        gap=hinge_gap,
        knuckle_diam=hinge_diameter,
        pin_diam=hinge_hole,
        clearance=assembly_gap,
        teardrop=UP,
        anchor=BOT
    );
}

module body_hinge() {
    translate([
        0,
        hinge_axis_y - hinge_native_axis_y,
        hinge_axis_z - hinge_native_axis_z
    ])
        hinge_half(false);
}

module lid_hinge_closed() {
    translate([0, hinge_axis_y, hinge_axis_z])
        rotate([180, 0, 0])
            rotate([0, 0, 180])
                translate([0, -hinge_native_axis_y, -hinge_native_axis_z])
                    hinge_half(true);
}

module divider_key(clearance=0) {
    profile_width = divider_joint[0] / 2;
    scale_x = (profile_width + 2 * clearance) / profile_width;
    scale_y = (divider_joint[1] + 2 * clearance) / divider_joint[1];
    center_x = divider_joint[0] / 2;
    center_y = divider_joint[1] / 2;

    translate([-center_x, -center_y, 0])
        translate([center_x, center_y, 0])
            scale([scale_x, scale_y, 1])
                translate([-center_x, -center_y, 0])
                    dovetailJointA(divider_joint, 1);
}

module divider_socket_cuts() {
    for (y = divider_joint_y)
        translate([0, y, -eps])
            divider_key(latch_clearance);
}

module seat_instances() {
    for (x = seat_x)
        translate([x, seat_y, 0])
            import(seat_path, convexity=10);
}

module latch_socket(orientation) {
    rabbit_clip(
        "socket",
        length=latch_length,
        width=latch_width,
        snap=latch_snap,
        thickness=latch_thickness,
        depth=latch_depth + 0.4,
        clearance=latch_clearance,
        compression=0.1,
        orient=orientation,
        anchor=BOTTOM
    );
}

module latch_clip(print_orientation=true) {
    rabbit_clip(
        "double",
        length=latch_length,
        width=latch_width,
        snap=latch_snap,
        thickness=latch_thickness,
        depth=latch_depth,
        compression=0.1,
        orient=print_orientation ? BACK : UP,
        anchor=CENTER
    );
}

module body_shell() {
    difference() {
        rounded_prism(case_width, case_height, case_depth, corner_radius);
        translate([0, wall, back_wall])
            rounded_prism(
                case_width - 2 * wall,
                case_height - 2 * wall,
                case_depth - back_wall + eps,
                max(corner_radius - wall, 0.4)
            );
        for (x = seat_x)
            translate([x, seat_y, -eps])
                cylinder(h=back_wall + 2 * eps, r=seat_cut_radius);
        divider_socket_cuts();
    }
}

module body() {
    difference() {
        union() {
            body_shell();
            seat_instances();
            body_hinge();
            translate([-latch_boss_width / 2, 0, case_depth - latch_boss_height])
                cube([latch_boss_width, latch_depth + 1, latch_boss_height]);
        }
        translate([0, (latch_depth + 1) / 2, case_depth + eps])
            latch_socket(DOWN);
    }
}

module lid_plate_closed() {
    difference() {
        translate([0, 0, case_depth])
            rounded_prism(case_width, case_height, lid_thickness, corner_radius);
        notch_width = hinge_length / hinge_segments - hinge_gap + 2 * assembly_gap;
        for (i = [-3 : 2 : 3])
            translate([
                i * hinge_length / hinge_segments - notch_width / 2,
                case_height - hinge_diameter / 2,
                case_depth - eps
            ])
                cube([notch_width, hinge_diameter, lid_thickness + 2 * eps]);
    }
}

module lid_closed() {
    difference() {
        union() {
            lid_plate_closed();
            lid_hinge_closed();
            translate([-latch_boss_width / 2, 0, case_depth])
                cube([latch_boss_width, latch_depth + 1, latch_boss_height]);
            translate([0, case_height / 2 + 1.5, case_depth + lid_thickness - eps])
                text3d(
                    label,
                    h=0.4,
                    size=min(6, 42 / max(len(label), 1)),
                    font="Arial:style=Bold",
                    anchor=BOT
                );
        }
        translate([0, (latch_depth + 1) / 2, case_depth - eps])
            latch_socket(UP);
    }
}

module divider() {
    union() {
        translate([-divider_thickness / 2, wall, back_wall])
            cube([
                divider_thickness,
                case_height - 2 * wall,
                case_depth - back_wall - 0.5
            ]);
        for (y = divider_joint_y)
            translate([0, y, 0])
                divider_key(0);
    }
}

module lid_print() {
    translate([0, 0, -case_depth])
        lid_closed();
}

module latch_coupon() {
    difference() {
        translate([-14, 0, 0]) cube([latch_boss_width, latch_depth + 1, latch_boss_height]);
        translate([-9, (latch_depth + 1) / 2, latch_boss_height + eps])
            latch_socket(DOWN);
    }
    difference() {
        translate([4, 0, 0]) cube([latch_boss_width, latch_depth + 1, latch_boss_height]);
        translate([9, (latch_depth + 1) / 2, -eps])
            latch_socket(UP);
    }
    translate([0, 12, latch_width / 2]) latch_clip(true);
}

module body_collision_shape() {
    union() {
        body_shell();
        body_hinge();
        translate([-latch_boss_width / 2, 0, case_depth - latch_boss_height])
            cube([latch_boss_width, latch_depth + 1, latch_boss_height]);
    }
}

module lid_at_angle(open_angle=0) {
    translate([0, hinge_axis_y, hinge_axis_z])
        rotate([-open_angle, 0, 0])
            translate([0, -hinge_axis_y, -hinge_axis_z])
                lid_closed();
}

module divider_print() {
    translate([case_depth - back_wall - 0.5, 0, divider_thickness / 2])
        rotate([0, 90, 0])
            divider();
}

module assembly(open_angle=0) {
    color("gold") body();
    color("deepskyblue", 0.85)
        translate([0, hinge_axis_y, hinge_axis_z])
            rotate([-open_angle, 0, 0])
                translate([0, -hinge_axis_y, -hinge_axis_z])
                    lid_closed();
    color("mediumseagreen") divider();
    if (open_angle == 0)
        color("tomato")
            translate([0, (latch_depth + 1) / 2, case_depth])
                latch_clip(false);
}

if (part_id == 1) {
    body();
} else if (part_id == 2) {
    lid_print();
} else if (part_id == 3) {
    divider_print();
} else if (part_id == 4) {
    latch_clip(true);
} else if (part_id == 5) {
    assembly(0);
} else if (part_id == 6) {
    assembly(open_angle);
} else if (part_id == 7) {
    latch_coupon();
} else if (part_id == 8) {
    intersection() {
        body_collision_shape();
        lid_at_angle(0);
    }
} else if (part_id == 9) {
    intersection() {
        body_collision_shape();
        lid_at_angle(open_angle);
    }
} else {
    body();
    translate([case_width + 8, 0, 0]) lid_print();
    translate([case_width / 2 + 5, case_height + 8, 0]) divider_print();
    translate([case_width / 2 - 8, case_height + 14, 0]) latch_clip(true);
}
