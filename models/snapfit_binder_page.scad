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
page_width = 24;
page_thickness = 1.2;
spine_width = groove_width - 2 * clearance;
spine_height = groove_height - 2 * clearance;
detent_height = 0.25;
detent_length = 4.0;
neck_width = lip + 0.15;
page_offset_y = rail_depth + 1.0;
page_z = wall + groove_height / 2 - page_thickness / 2;

module rounded_plate(size, r = 0.9) {
    hull() {
        for (x = [r, size[0] - r])
        for (y = [r, size[1] - r])
            translate([x, y, 0]) cylinder(h = size[2], r = r);
    }
}

module binder() {
    // A vertical C-channel. The open slot faces +Y. The page body remains
    // outside the rail while only the spine slides through this channel.
    difference() {
        cube([rail_length, rail_depth, rail_height]);

        // Main spine cavity.
        translate([wall, -0.1, wall])
            cube([rail_length - 2 * wall, groove_width + 0.1, groove_height]);

        // Front opening, leaving upper and lower lips.
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
    // The spine bead enters the binder groove. The thin neck passes through
    // the front slot. The page body starts outside the rail, so it cannot
    // collide with the rail's lower wall during sliding.
    translate([0, page_offset_y, page_z])
        rounded_plate([page_length, page_width, page_thickness], 0.8);

    translate([0, 0, wall + clearance])
        cube([page_length, spine_width, spine_height]);

    translate([0, spine_width - 0.05, page_z])
        cube([page_length, page_offset_y - spine_width + 0.1, page_thickness]);

    // Removable lock bumps. If this is too tight, reduce detent_height first.
    translate([5, spine_width - 0.05, wall + clearance + spine_height / 2 - 0.7])
        cube([detent_length, detent_height, 1.4]);
    translate([page_length - 5 - detent_length, spine_width - 0.05, wall + clearance + spine_height / 2 - 0.7])
        cube([detent_length, detent_height, 1.4]);
}

module both_preview() {
    binder();
    translate([0, rail_depth + page_width + 10, 0]) page();
}

if (part_id == 1) {
    binder();
} else if (part_id == 2) {
    page();
} else {
    both_preview();
}
