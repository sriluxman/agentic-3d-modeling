/*simple Snap library based on "Snap-Fit Joints for Plastics - A Design Guid" by Bayer MaterialScience LLC 
  http://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf
 
 on http://www.thingiverse.com/thing:1860118
 
    by fpetrac Fausto Petraccone fpetrac@gmail.com 
    Licensed under the Creative Commons - Attribution - Non-Commercial license.
*/

/*Rev
    SnapLib 0.36.scad: added SnapHoleY function  
    SnapLib 0.35.scad: on RSnapY added a check to avioid interference of lobes during closure; on RRSnappY added a check to avioid overlapped lobes.
    SnapLib 0.30.scad  added function Hsnap and Snap to calculate the snap H or Y for cantilever snap
    SnapLib 0.25.scad  added Scale factor f to reduce the calculate value h or y (this mantain the snap on unbreakable zone when f>1)
    SnapLib 0.20.scad  Bug Fix
    SnapLib 0.10.scad  added RSnapY RRSnapY
    SnapLib 0.00.scad  first release
*/


/*
eps=0.5*6/100;//Elongation at break of PLA=6%
eps=0.5*12/100;//Elongation at break of ABS=12%
eps=0.5*18/100;//Elongation at break of PETG=18%
*/

eps=0.5*6/100;//Elongation at break of PLA=6%


function Hsnap(l,y,f)= (1.09/f)*(eps*pow(l,2))/(y);
function Ysnap(l,h,f)= (1.09/f)*(eps*pow(l,2))/(h);

//SnapH(l,y,a,b,f=1) Define y calculate h and divide the calculte h value to a factor f
module SnapH(l,y,a,b,f=1)   
{
    h=Hsnap(l,y,f);
    p=y;
    echo("h is",h);
linear_extrude(height = b, center = f, convexity = 10, twist = 0)
polygon([[0,0],[l,0],[l,y],[l+p,y],[l+p+(y+h/4)/tan(a),-h/4],[l,-h/2],[0,-h]]);
}
//SnapY(l,h,a,b,f=1) Define h calculate y and divide the calculte y value to a factor f
module SnapY(l,h,a,b,f=1)
{
    y=Ysnap(l,h,f);
    p=y;
    echo("y is", y);
linear_extrude(height = b, center = f, convexity = 10, twist = 0)
polygon([[0,0],[l,0],[l,y],[l+p,y],[l+p+(y+h/4)/tan(a),-h/4],[l,-h/2],[0,-h]]);
}
//SnapHoleY(l,h,a,b,f=1,Pr=2) Define h calculate y and divide the calculte y value to a factor f the total hole depth is h*PR
module SnapHoleY(l,h,a,b,f=1,Pr=2){
        //%SnapY(l,h,a,b);  
        y=Ysnap(l,h,f);
        YY=Pr*h;//depth Y;
        XX=1.1*(y+(y+h/4)/tan(a)); //Altezza totale +10%
        ZZ=0+b; //largezza piu tolleranza
        union(){
            translate([0,-YY,(b-ZZ)/2])cube([l,YY,ZZ],center=false); //gambo
            translate([l,-YY,(b-ZZ)/2])cube([XX,YY+y,ZZ],center=false);//testa
        }    
 }



//Define h calculate y and divide the calculated value to f
module RSnapY(l,h,a,Lobi,r2,f=1,K2=2)   
{
    Theta=180/Lobi;
    y=(1.64/f)*K2*(eps*pow(l,2))/(r2);
    p=y;
    echo("y is", y);
    echo("r1/r2",(r2-h)/r2);
    echo("Theta", Theta);
    echo("r2-h",(r2-h));
    if(((r2-h)>y)&&(h<r2)){ //(r2-h)>y should be (r2-h/2)>y and  h<r2 for scad problem
      for(f=[0:1:Lobi])
          rotate([0,0,Theta*2*f])
              rotate_extrude(angle = Theta, convexity = 2,$fn=200)
                  translate([r2,0,0])
                      mirror([1,-1,0])
                          polygon([[0,0],[l,0],[l,y],[l+p,y],[l+p+(y+h/4)/tan(a),-h/4],[l,-h/2],[0,-h]]);
    }
    else{
      echo ("<b>WARNING:</b>");
      echo("y should be < r2-h ");
      echo("h should be < r2 ");
    }
}
//Define h calculate y and divide the calculated value to f
module RRSnapY(l,h,a,Lobi,r2,f=1,K1=2)
{
    Theta=180/Lobi;
    y=(1.64/f)*K1*(eps*pow(l,2))/(r2);
    p=y;
    echo("y is", y);
    echo("r1/r2",(r2-h)/r2);
    echo("Theta", Theta);
    echo("r2-y",(r2-y));
    if(y<r2){
      for(f=[0:1:Lobi])
          rotate([0,180,Theta*2*f])
              rotate_extrude(angle = Theta, convexity = 2,$fn=200)
                  translate([r2,0,0])
                      mirror([1,1,0])
                          polygon([[0,0],[l,0],[l,y],[l+p,y],[l+p+(y+h/4)/tan(a),-h/4],[l,-h/2],[0,-h]]);
  }
      else{
      echo ("<b>WARNING:</b>");
      echo("y should be < r2 ");
      }
}
