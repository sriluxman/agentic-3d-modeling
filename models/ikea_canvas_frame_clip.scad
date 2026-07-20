$fn = 48;
part_id = 0; // 0 four-up plate, 1 single clip, 2 fit coupon, 3 assembly, 4 profile

frame_depth = 15.5;
frame_gap = 16.2;
frame_face_width = 40;
taper_length = 6;
canvas_reach = 30;
narrow_gap = 3.0;

clip_width = 20;
clip_thickness = 2.8;

coupon_gaps = [3.0, 3.5, 4.0];
coupon_arm_length = 16;
coupon_reach = 12;
coupon_taper = 4;
coupon_width = 8;

eps = 0.05;

module capsule_2d(start, end, diameter) {
    hull() {
        translate(start) circle(d=diameter);
        translate(end) circle(d=diameter);
    }
}

module clip_profile_2d(
    gap=frame_gap,
    frame_width=frame_face_width,
    transition=taper_length,
    reach=canvas_reach,
    end_gap=narrow_gap
) {
    radius = clip_thickness / 2;
    wide_x = gap / 2 + radius;
    narrow_x = end_gap / 2 + radius;
    bridge_y = -radius;
    taper_end = frame_width + transition;
    reach_end = taper_end + reach;

    union() {
        capsule_2d([-wide_x, bridge_y], [wide_x, bridge_y], clip_thickness);
        for (side = [-1, 1]) {
            capsule_2d(
                [side * wide_x, bridge_y],
                [side * wide_x, frame_width],
                clip_thickness
            );
            capsule_2d(
                [side * wide_x, frame_width],
                [side * narrow_x, taper_end],
                clip_thickness
            );
            capsule_2d(
                [side * narrow_x, taper_end],
                [side * narrow_x, reach_end],
                clip_thickness
            );
        }
    }
}

module canvas_clip(gap=frame_gap, width=clip_width) {
    linear_extrude(width)
        clip_profile_2d(gap=gap);
}

module fit_coupon(end_gap, marker_count) {
    difference() {
        linear_extrude(coupon_width)
            clip_profile_2d(
                gap=frame_gap,
                frame_width=coupon_arm_length,
                transition=coupon_taper,
                reach=coupon_reach,
                end_gap=end_gap
            );

        for (marker = [0 : marker_count - 1])
            translate([
                (marker - (marker_count - 1) / 2) * 2.4,
                -clip_thickness / 2,
                -eps
            ])
                cylinder(d=0.9, h=coupon_width + 2 * eps, $fn=18);
    }
}

module coupon_plate() {
    for (index = [0 : len(coupon_gaps) - 1])
        translate([index * 28, 0, 0])
            fit_coupon(coupon_gaps[index], index + 1);
}

module four_clip_plate() {
    for (column = [0 : 1])
        for (row = [0 : 1])
            translate([column * 27, row * 84, 0])
                canvas_clip();
}

module assembly_view() {
    color("burlywood")
        translate([-frame_depth / 2, 0, 2])
            cube([frame_depth, frame_face_width, clip_width - 4]);
    color("linen")
        translate([-narrow_gap / 2, frame_face_width + taper_length, 2])
            cube([narrow_gap, canvas_reach + 4, clip_width - 4]);
    color("orange") canvas_clip();
}

if (part_id == 1) {
    canvas_clip();
} else if (part_id == 2) {
    coupon_plate();
} else if (part_id == 3) {
    assembly_view();
} else if (part_id == 4) {
    linear_extrude(1) clip_profile_2d();
} else {
    four_clip_plate();
}
