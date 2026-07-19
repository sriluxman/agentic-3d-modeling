/*
Small-scale snap-fit binder + page experiment.

Concept:
  - The binder is a short rail with a C-shaped side groove.
  - The page is a thin strip with a spine bead that slides into the groove.
  - Small top/bottom detents on the page bead create removable locking.

Part selector:
  part_id = 0; // preview both parts
  part_id = 1; // binder rail
  part_id = 2; // page strip
*/

$fn = 48;

part_id = 0;

clearance = 0.35;
rail_length = 50;
rail_height = 12;
rail_depth = 8;
wall = 2.0;

groove_width = 3.2;
groove_height = 7.0;
lip = 0.9;

page_length = 46;
page_width = 28;
page_thickness = 1.2;
spine_width = groove_width - 2 * clearance;
spine_height = groove_height - 2 * clearance;
detent_height = 0.45;
detent_length = 4.0;

module rounded_plate(size, r = 0.9) {
    hull() {
        for (x = [r, size[0] - r])
        for (y = [r, size[1] - r])
            translate([x, y, 0]) cylinder(h = size[2], r = r);
    }
}

module binder() {
    difference() {
        rounded_plate([rail_length, rail_depth, rail_height], 1.0);

        // Main channel.
        translate([wall, -0.1, wall])
            cube([rail_length - 2 * wall, groove_width + 0.1, groove_height]);

        // Front slot, leaving top/bottom lips to capture the page spine.
        translate([wall, -0.2, wall + lip])
            cube([rail_length - 2 * wall, rail_depth, groove_height - 2 * lip]);

        // Entry chamfers at both ends so the page starts more easily.
        translate([-0.1, -0.2, wall + lip])
            cube([2.2, rail_depth, groove_height - 2 * lip]);
        translate([rail_length - 2.1, -0.2, wall + lip])
            cube([2.2, rail_depth, groove_height - 2 * lip]);
    }

    // End-stop bumps inside the rail; these are intentionally small.
    translate([5, groove_width - 0.05, wall + groove_height / 2 - 0.7])
        cube([detent_length, 0.55, 1.4]);
    translate([rail_length - 5 - detent_length, groove_width - 0.05, wall + groove_height / 2 - 0.7])
        cube([detent_length, 0.55, 1.4]);
}

module page() {
    // A tiny page, printed flat, with a thicker snap spine on the left edge.
    rounded_plate([page_length, page_width, page_thickness], 0.8);

    translate([0, 0, page_thickness])
        cube([page_length, spine_width, spine_height]);

    // Removable lock bumps. If this is too tight, reduce detent_height first.
    translate([5, spine_width - 0.05, page_thickness + spine_height / 2 - 0.7])
        cube([detent_length, detent_height, 1.4]);
    translate([page_length - 5 - detent_length, spine_width - 0.05, page_thickness + spine_height / 2 - 0.7])
        cube([detent_length, detent_height, 1.4]);
}

module both_preview() {
    binder();
    translate([0, 20, 0]) page();
}

if (part_id == 1) {
    binder();
} else if (part_id == 2) {
    page();
} else {
    both_preview();
}

