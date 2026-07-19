include <BOSL2/std.scad>
include <BOSL2/threading.scad>

$fn = 48;
part_id = 0; // 0 print plate, 1 India, 2 Austria, 3 assembled, 4 exploded, 5 thread coupon, 6 collision

cube_size = 36;
half_width = cube_size / 2;
flag_relief = 0.45;

thread_diameter = 14;
thread_length = 12;
thread_pitch = 3;
thread_depth = 1;
thread_angle = 45;
thread_slop = 0.125; // BOSL2 adds 2 * slop radially to an internal thread.
socket_spin = 180; // Align the internal thread valley with the male crest.

collar_diameter = 17;
collar_length = 1.1;
collar_clearance = 0.25;
collar_recess_depth = 1.3;
eps = 0.04;

india_saffron = "#FF8C1A";
india_green = "#138808";
chakra_blue = "#000080";
austria_red = "#C8102E";

module thread_male(length=thread_length) {
    trapezoidal_threaded_rod(
        d=thread_diameter,
        l=length,
        pitch=thread_pitch,
        thread_depth=thread_depth,
        thread_angle=thread_angle,
        bevel2=true,
        anchor=BOT,
        orient=RIGHT
    );
}

module thread_socket(length=thread_length + 1) {
    trapezoidal_threaded_rod(
        d=thread_diameter,
        l=length,
        pitch=thread_pitch,
        thread_depth=thread_depth,
        thread_angle=thread_angle,
        internal=true,
        bevel1=true,
        spin=socket_spin,
        anchor=BOT,
        orient=RIGHT,
        $slop=thread_slop
    );
}

module india_core() {
    union() {
        translate([-half_width, 0, 0]) cube([half_width, cube_size, cube_size]);
        translate([-eps, cube_size / 2, cube_size / 2])
            rotate([0, 90, 0]) cylinder(h=collar_length + eps, d=collar_diameter);
        translate([0, cube_size / 2, cube_size / 2]) thread_male();
    }
}

module austria_core() {
    difference() {
        translate([0, 0, 0]) cube([half_width, cube_size, cube_size]);
        translate([-eps, cube_size / 2, cube_size / 2])
            rotate([0, 90, 0])
                cylinder(
                    h=collar_recess_depth + eps,
                    d=collar_diameter + 2 * collar_clearance
                );
        translate([-eps, cube_size / 2, cube_size / 2])
            thread_socket(thread_length + 1.5);
    }
}

module front_panel(x, z, width, height) {
    translate([x, -flag_relief, z]) cube([width, flag_relief + eps, height]);
}

module chakra_2d() {
    union() {
        difference() {
            circle(r=4.6);
            circle(r=4.05);
        }
        circle(r=0.8);
        for (angle = [0 : 15 : 345])
            rotate(angle)
                translate([0, 2.35])
                    square([0.42, 3.7], center=true);
    }
}

module chakra() {
    translate([-half_width / 2, eps, cube_size / 2])
        rotate([90, 0, 0])
            render(convexity=10)
                linear_extrude(flag_relief + 0.25)
                    chakra_2d();
}

module india_flag_surfaces() {
    front_panel(-half_width, 2 * cube_size / 3, half_width, cube_size / 3);
    front_panel(-half_width, 0, half_width, cube_size / 3);
    chakra();
}

module austria_flag_surfaces() {
    front_panel(0, 2 * cube_size / 3, half_width, cube_size / 3);
    front_panel(0, 0, half_width, cube_size / 3);
}

module india_solid() {
    union() {
        india_core();
        india_flag_surfaces();
    }
}

module austria_solid() {
    union() {
        austria_core();
        austria_flag_surfaces();
    }
}

module india_colored() {
    color("white") india_core();
    color(india_saffron) front_panel(-half_width, 2 * cube_size / 3, half_width, cube_size / 3);
    color(india_green) front_panel(-half_width, 0, half_width, cube_size / 3);
    color(chakra_blue) chakra();
}

module austria_colored() {
    color("white") austria_core();
    color(austria_red) austria_flag_surfaces();
}

module india_print(colored=false) {
    translate([0, 0, half_width])
        rotate([0, -90, 0])
            if (colored) india_colored(); else india_solid();
}

module austria_print(colored=false) {
    translate([0, 0, half_width])
        rotate([0, 90, 0])
            if (colored) austria_colored(); else austria_solid();
}

module thread_coupon() {
    // Male coupon: same thread, printed vertically from a compact grip disc.
    translate([-12, 0, 0]) {
        cylinder(h=4, d=20);
        translate([0, 0, 4])
            trapezoidal_threaded_rod(
                d=thread_diameter,
                l=thread_length,
                pitch=thread_pitch,
                thread_depth=thread_depth,
                thread_angle=thread_angle,
                bevel2=true,
                anchor=BOT
            );
    }

    // Female coupon prints with its opening upward, like the production half.
    translate([12, 0, 0])
        difference() {
            cylinder(h=16, d=20);
            translate([0, 0, 16 + eps])
                trapezoidal_threaded_rod(
                    d=thread_diameter,
                    l=thread_length + 1.5,
                    pitch=thread_pitch,
                    thread_depth=thread_depth,
                    thread_angle=thread_angle,
                    internal=true,
                    bevel1=true,
                    spin=socket_spin,
                    anchor=BOT,
                    orient=DOWN,
                    $slop=thread_slop
                );
        }
}

module assembled(colored=true) {
    if (colored) {
        india_colored();
        austria_colored();
    } else {
        india_solid();
        austria_solid();
    }
}

module exploded() {
    translate([-8, 0, 0]) india_colored();
    translate([8, 0, 0]) austria_colored();
}

if (part_id == 1) {
    india_print(false);
} else if (part_id == 2) {
    austria_print(false);
} else if (part_id == 3) {
    assembled(true);
} else if (part_id == 4) {
    exploded();
} else if (part_id == 5) {
    thread_coupon();
} else if (part_id == 6) {
    intersection() {
        india_solid();
        austria_solid();
    }
} else if (part_id == 10) {
    translate([-24, 0, 0])
        translate([0, 0, half_width]) rotate([0, -90, 0]) india_core();
} else if (part_id == 11) {
    translate([-24, 0, 0])
        translate([0, 0, half_width]) rotate([0, -90, 0])
            front_panel(-half_width, 2 * cube_size / 3, half_width, cube_size / 3);
} else if (part_id == 12) {
    translate([-24, 0, 0])
        translate([0, 0, half_width]) rotate([0, -90, 0])
            front_panel(-half_width, 0, half_width, cube_size / 3);
} else if (part_id == 13) {
    translate([-24, 0, 0])
        translate([0, 0, half_width]) rotate([0, -90, 0]) chakra();
} else if (part_id == 14) {
    translate([24, 0, 0])
        translate([0, 0, half_width]) rotate([0, 90, 0]) austria_core();
} else if (part_id == 15) {
    translate([24, 0, 0])
        translate([0, 0, half_width]) rotate([0, 90, 0]) austria_flag_surfaces();
} else {
    translate([-24, 0, 0]) india_print(true);
    translate([24, 0, 0]) austria_print(true);
}
