include <utils.scad>;
$fa = 1;
$fs = .2;

W = 56;
H = 42;
r = 4.0;
R = 8;
T = 15;
wallT=1.6;
tiecornerR = 10;

pivot_x = -W/2 + R;
pivot_y = H/2 - R;

bearingBore=5;
bearingD = 11;
bearingT = 4;
TIGHTSP = .1;
MEDSP = .3;

function corner_r(R_, r_) = [[pivot_x, pivot_y, R_], [W/2-r, H/2-r, r_], [-W/2+r, -H/2+r, r_], [W/2-r, -H/2+r, r_]];

module base2d(wallT=0){
  
  assert(r > wallT);
  R_ = R - wallT;
  r_ = r - wallT; 

  
  hull()
  for (pos_r=corner_r(R_, r_)){
    translate([pos_r[0], pos_r[1]]) circle(pos_r[2]);
  }
}

module bearingaxle(){
  translate([pivot_x, pivot_y, T/2])
  mirror([0,0,1])
  {
    cylinder(h=T/2, d=bearingBore-TIGHTSP*2);
    cylinder(h=wallT+MEDSP, d=bearingBore+2);
  }
}

module tiecorner(R, key="cut"){
  R_ = key=="cut" ? R - wallT : R;

  translate([W/2, H/2, 0])
  if (key=="cut"){cylinder(h=T-2*wallT, r=R_, center=true);}
  else if (key=="wall"){
    rotate([0,0,180])
    intersection(){ 
      difference(){
        cylinder(h=T/2, r=R_);
        cylinder(h=T/2, r=R_-wallT);
      }
      cube(100);
    }
  } 
}

module finger(key="finger", rotAngle=0){
  addr = key=="cut" ? MEDSP: 0;
  r = 1;
 
  D1 = 8;
  D2 = 3;
  L = 50;
  module base2d(){
    module p1(){translate([(bearingD+wallT)/2 - D1/2, R + D1/2 +2*MEDSP]) circle(d=D1 - 2*r);}
    module p2(){translate([(bearingD+wallT)/2 - D2/2 - L, R + D2/2 + 2*MEDSP]) circle(d=D2 - 2*r);}
    module p3(){circle(d=bearingD + 2*wallT - 2*r);}

    module base(){
      hull(){p1(); p2();}
      hull(){p3(); p1();}
    }
    
    mirror([1,0,0]) offset(-(r+addr)) offset(2*(r+addr)) base();
  }

  module spacer(){
    linear_extrude(height=fingerT - 2*bearingT)
    difference(){
      circle(d=bearingD-4*TIGHTSP); 
      circle(d=bearingBore+2*MEDSP); 
    }
  }
  fingerT = key=="cut" ? T-2*wallT : T-2*(wallT+MEDSP+TIGHTSP);
  translate([pivot_x, pivot_y]) rotate([0,0,rotAngle]) 
  {
  linear_extrude(height=fingerT, center=true)
  difference(){
    base2d();
    if (key=="finger") circle(d=bearingD+TIGHTSP*2); 
    else if (key=="cut") circle(d=bearingBore+4); 
  };
  spacer();
  }
} 


module closebolts(key="bars", side="top"){
  boltD = key!="cut" ? BOLT25TIGHT : side=="top" ? BOLT25TIGHT : BOLT25LOOSE ; 
  for (pos=corner_r(R, r)){
   translate([pos[0], pos[1],0]) 
   if (key=="cut"){translate([0,0,-T/2]) bolt(T - boltD/2 - .5, boltD,  .30);}
   else if (key=="bars"){cylinder(h=T/2, d=boltD+2*wallT);}
  }  
  
}

module switch(key="cut", side="top"){
  swW = 12.8;
  swH = 8;
  swT = 7;
  sideT = 6;
  boltD = side=="top" ? BOLT25TIGHT : BOLT25LOOSE;
  module mount(){translate([0,0,T/4]) cube([swW + 2*sideT, swH, T/2], center=true);}
  module bolts(){for (i=[-1,1]) translate([i*(swW/2 + boltD),0, -T/2]) bolt(T-boltD/2 - .5, boltD, .3);}
  module cut(){cube([swW + 2*TIGHTSP, 2*swH, swT+2*TIGHTSP], center=true);}

  sx = -2.5;
  translate([sx, -swH/2 + H/2, 0]){
  if (key=="mount") mount();
  else if (key=="cut"){bolts(); cut();}
  }
}

module side(side="bottom"){
  ledPos = [W/2-13, H/2 - 5];
  ledD = 3 + 2*TIGHTSP;
  module side_(){
    union(){
      difference(){
        linear_extrude(height = T/2) base2d();
        translate([0,0,-1]) linear_extrude(height = T/2 - wallT + 1) base2d(wallT);
      }
      closebolts(key="bars", side=side);
    }
    tiecorner(tiecornerR, "wall");
    switch(key="mount", side=side);
    bearingaxle();
    if (side=="top"){nano("poles");}
  }

  //bearingaxle();
  difference(){
    if (side=="bottom"){mirror([0,0,1]) side_();}    
    else if (side=="top") side_();
    tiecorner(tiecornerR);
    for (rot=[0,40]) finger("cut", rot); 
    closebolts("cut", side=side);
    switch(key="cut", side=side);
    nano("bolts");
    if (side=="top") translate(ledPos) cylinder(h=2*T, d=ledD, center=true);
  }
}


module nano(key){translate([W/2-25,-H/2+17,T/2]) mirror([0,0,1]) nanoble(wallT + 2, key=key);}

side("top");
translate([0,0,-.1]) side("bottom");
//side("bottom");
//finger("cut");
finger("finger");

