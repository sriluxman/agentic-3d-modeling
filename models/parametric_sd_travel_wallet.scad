$fn = 48;
part_id = 0; // 0 plate, 1 tray, 2 sleeve, 3 assembled, 4 exploded, 5 collision, 6 latch coupon

card_count = 5;
card_dimensions = [24, 32, 2.1]; // width, height, thickness

slot_clearance = 0.25;
card_side_clearance = 0.30;
divider_thickness = 1.0;
divider_embed = 0.3;
wall = 1.6;
floor_thickness = 1.2;
flange_thickness = 1.6;
flange_overhang = 2.0;
card_top_clearance = 0.8;
card_exposure = 6.0;
front_access_drop = 3.0;
corner_radius = 2.0;

sleeve_clearance = 0.35;
sleeve_wall = 1.6;
sleeve_roof = 1.6;
sleeve_top_clearance = 0.6;

tongue_width = 7.0;
tongue_slit = 0.55;
tongue_bottom = 3.2;
tongue_anchor = 14.5;
bump_radius = 1.35;
bump_projection = 0.75;
bump_embed = 0.8;
bump_z = 5.2;
window_width = 9.0;
window_height = 4.2;

card_width = card_dimensions[0];
card_height = card_dimensions[1];
card_thickness = card_dimensions[2];
slot_width = card_thickness + 2 * slot_clearance;
inner_width = card_count * slot_width + (card_count - 1) * divider_thickness;
inner_depth = card_width + 2 * card_side_clearance;
tray_width = inner_width + 2 * wall;
tray_depth = inner_depth + 2 * wall;
floor_z = flange_thickness + floor_thickness;
card_top = floor_z + card_height;
tray_wall_height = card_top - card_exposure;
protected_height = card_top + card_top_clearance;

sleeve_inner_width = tray_width + 2 * sleeve_clearance;
sleeve_inner_depth = tray_depth + 2 * sleeve_clearance;
sleeve_outer_width = sleeve_inner_width + 2 * sleeve_wall;
sleeve_outer_depth = sleeve_inner_depth + 2 * sleeve_wall;
sleeve_inner_top = protected_height + sleeve_top_clearance;
sleeve_top = sleeve_inner_top + sleeve_roof;

eps = 0.05;

module rounded_prism(width, depth, height, radius) {
    linear_extrude(height)
        offset(r=radius)
            square([width - 2 * radius, depth - 2 * radius], center=true);
}

module tongue_cutouts() {
    front_y = -tray_depth / 2 - eps;
    cut_depth = wall + 2 * eps;
    for (side = [-1, 1])
        translate([
            side * tongue_width / 2 - tongue_slit / 2,
            front_y,
            tongue_bottom
        ])
            cube([tongue_slit, cut_depth, tongue_anchor - tongue_bottom]);

    translate([
        -tongue_width / 2 - tongue_slit / 2,
        front_y,
        tongue_bottom - tongue_slit / 2
    ])
        cube([tongue_width + tongue_slit, cut_depth, tongue_slit]);
}

module front_access_cut() {
    cut_width = tray_width - 2 * corner_radius;
    translate([
        -cut_width / 2,
        -tray_depth / 2 - eps,
        tray_wall_height - front_access_drop
    ])
        cube([
            cut_width,
            wall + 2 * eps,
            front_access_drop + eps
        ]);
}

module tray_shell() {
    difference() {
        union() {
            rounded_prism(
                tray_width + 2 * flange_overhang,
                tray_depth + 2 * flange_overhang,
                flange_thickness,
                corner_radius + flange_overhang
            );
            rounded_prism(tray_width, tray_depth, tray_wall_height, corner_radius);
        }

        translate([0, 0, floor_z])
            rounded_prism(
                tray_width - 2 * wall,
                tray_depth - 2 * wall,
                tray_wall_height - floor_z + eps,
                max(corner_radius - wall, 0.4)
            );
        tongue_cutouts();
        front_access_cut();
    }
}

module dividers() {
    divider_height = tray_wall_height - floor_z;
    for (index = [1 : card_count - 1]) {
        x = -inner_width / 2 + index * slot_width + (index - 1) * divider_thickness;
        translate([x, -inner_depth / 2, floor_z - divider_embed])
            cube([divider_thickness, inner_depth, divider_height + divider_embed]);
    }
}

module latch_bump() {
    translate([0, -tray_depth / 2 + bump_embed, bump_z])
        rotate([90, 0, 0])
            cylinder(h=bump_projection + bump_embed, r=bump_radius);
}

module tray() {
    union() {
        tray_shell();
        dividers();
        latch_bump();
    }
}

module sleeve_window_cut() {
    translate([
        -window_width / 2,
        -sleeve_outer_depth / 2 - eps,
        bump_z - window_height / 2
    ])
        cube([window_width, sleeve_wall + 2 * eps, window_height]);
}

module sleeve() {
    difference() {
        translate([0, 0, flange_thickness])
            rounded_prism(
                sleeve_outer_width,
                sleeve_outer_depth,
                sleeve_top - flange_thickness,
                corner_radius + sleeve_clearance + sleeve_wall
            );
        translate([0, 0, flange_thickness - eps])
            rounded_prism(
                sleeve_inner_width,
                sleeve_inner_depth,
                sleeve_inner_top - flange_thickness + eps,
                corner_radius + sleeve_clearance
            );
        sleeve_window_cut();
    }
}

module sleeve_print() {
    translate([0, 0, sleeve_top])
        rotate([180, 0, 0])
            sleeve();
}

module card_dummy(index) {
    x = -inner_width / 2
        + index * (slot_width + divider_thickness)
        + slot_width / 2;
    color(index % 2 == 0 ? "midnightblue" : "slategray")
        translate([x - card_thickness / 2, -card_width / 2, floor_z])
            cube([card_thickness, card_width, card_height]);
}

module assembly(show_cards=true) {
    color("gold") tray();
    color("deepskyblue", 0.38) sleeve();
    if (show_cards)
        for (index = [0 : card_count - 1]) card_dummy(index);
}

module exploded() {
    color("gold") tray();
    color("deepskyblue", 0.55)
        translate([0, 0, protected_height + 8]) sleeve();
    for (index = [0 : card_count - 1]) card_dummy(index);
}

module latch_coupon() {
    // Exact production latch section, shortened to reduce preflight cost.
    intersection() {
        tray();
        translate([-7, -tray_depth / 2 - flange_overhang - 1, 0])
            cube([14, wall + flange_overhang + 4, 18]);
    }
    translate([20, 0, -flange_thickness])
        union() {
            intersection() {
                sleeve();
                translate([-7, -sleeve_outer_depth / 2 - 1, flange_thickness])
                    cube([14, sleeve_wall + 4, 13]);
            }
            translate([-7, -sleeve_outer_depth / 2 - 1, flange_thickness])
                cube([14, sleeve_wall + 4, 1.2]);
        }
}

if (part_id == 1) {
    tray();
} else if (part_id == 2) {
    sleeve_print();
} else if (part_id == 3) {
    assembly(true);
} else if (part_id == 4) {
    exploded();
} else if (part_id == 5) {
    intersection() {
        tray();
        sleeve();
    }
} else if (part_id == 6) {
    latch_coupon();
} else {
    translate([-18, 0, 0]) tray();
    translate([18, 0, 0]) sleeve_print();
}
