
// BOLTS:
BOLT15TIGHT = 1.4;
BOLT3TIGHT=2.9;
BOLT3LOOSE=3.05;
BOLT25TIGHT = 2.30; // 2.35
BOLT25LOOSE = 2.60;


module generalel(dims, mountpos, boltD=BOLT3TIGHT, H=2, key="mockup", boltH=0, poleD=0){
	
	poleD = poleD==0 ? boltD*2 : poleD;
	module poles(){
		for (p=mountpos){
			translate(p) cylinder(h=H, d=poleD);
		}
	}

	module bolts(){
		boltH = boltH == 0 ? H - .5 : boltH;
		
		color("Gray")	
		for (p=mountpos){
			translate(p) translate([0,0,H]) mirror([0,0, 1]) bolt(boltH, boltD, -boltD/2);
		}
	}
	
	translate([-dims[0]/2, -dims[1]/2, 0])
	if (key=="mockup"){
		echo("mckup");
		poles();
		color("Navy")
		translate([0,0,H]) cube(dims);
	}
	else if (key=="bolts"){bolts();}
	else if (key=="poles"){poles();}
	else if (key=="board"){
    		color("Navy")
		translate([0,0,H]) cube(dims);
	}
}

module nanoble(H=5, key="mockup", boltH=0, boltD=BOLT15TIGHT){
        dwall=1.5;
	dims = [43.4, 18, 2];
	mountpos = [[dwall, dwall], [dims[0]-dwall, dwall], [dwall, dims[1]-dwall], [dims[0]-dwall, dims[1]-dwall]];
	//boltH= boltH==0 ? H : boltH; //  + 1.5;
	color("DarkSlateGray")	
	generalel(dims, mountpos, boltD=boltD, H=H, key=key, boltH=boltH, poleD=4);
        if (key=="bolts"){
          translate([dims[0]/2,0,H+4])
          rotate([0,90,0])
          rounded_cutter(20, 8, 12, 1);
        }

}
module rounded_cutter(L, W, T, r){
  assert(min(W,T)>2*r);

  linear_extrude(height=L, center=true)
  offset(r)
  square([W-2*r, T-2*r],center=true);

}
module bolt(h, d, sink, baseL=5, key="csunk"){
   	
	// Expand the bolt sink hole by this amount: 
	sinkExpFac = 1.1;
	
	// Gray bolts
    	color("Gray")
    	translate([0,0,sink])
    	union(){
		// bolt thread
		translate([0,0,d/2]) cylinder(h=h, r=d/2);
		// bolt base
		if (key=="csunk"){cylinder(h=d/2, r1=d*sinkExpFac, r2=d/2*sinkExpFac);}
		else if (key=="flat"){cylinder(h=d/2 - .2, r=d*sinkExpFac);}
		
		translate([0,0,-baseL - sink]) cylinder(h=baseL + sink, r=d*sinkExpFac);
    	}
}


