"""
Conversion of UTM GPS Coordinates to DD / DMS GPS Coordinates
"""

def utm_to_DD(x, y, zone, mode = "DD"):
	"""
	x - UTM easting
	y - UTM northing
	zone - current UTM zone
	mode - conversion to Decimal Degrees (mode = DD) or DMS (mode = DMS)
	"""
	
	import math

	# Check for validity of UTM coordinates
	# TODO: Check for correct range of coordinates
	try:
		x = float(x)
		y = float(y)
	except:
		print("The UTM coordinates given are invalid.")
	
	# (x, a, b, k0, e, e1sq, M, mu, e1, e1a, e2, j1, j2, j3, j4, fp, C1, T1, R1, R2, N1) = 0
	# (N2, D, Q1, Q2, Q3, Q4, Q5, Q6, Q7, lat, longi, longi0) = 0 	
	x0 = 500000 - x;
	a = 6378137;
	b = 6356752.3142;
	k0 = 0.9996;
	e = 0.081819191; # double e = math.sqrt(1-math.pow(b, 2)/math.pow(b, 2));
	e1sq = 0.006739497;
	longi0 = -177 + 6*(zone-1); # zones
	    
	# Calculate the Meridional Arc
	M = y/k0;
	
	# Calculate the footprint latitude
	mu = M/(a*(1 - (math.pow(e,2))/4 - 3*(math.pow(e,4))/64 - 5*(math.pow(e,6))/256));
	e1a = 1-(math.pow(e,2));
	e1 = (1-(math.pow(e1a, 0.5))) /(1+(math.pow(e1a, 0.5)));
	
	j1 = 3*e1/2-27*math.pow(e1,3)/32;
	# j2 = 21*math.pow(e1,2)/2-55*math.pow(e1,4)/32; # error /2 = /16
	j2 = 21*math.pow(e1,2)/15-55*math.pow(e1,4)/32;
	j3 = 151*math.pow(e1,3)/96;
	j4 = 1097*math.pow(e1,4)/512;
	
	fp = mu + j1*math.sin(2*mu) + j2*math.sin(4*mu) + j3*math.sin(6*mu) + j4*math.sin(8*mu);
	
	# Calculate Latitude and Longitude
	e2 = (math.pow(e,2))/e1a;
	C1 = e2*math.pow(math.cos(fp),2);
	T1 = math.pow(math.tan(fp),2);
	
	R2 = math.pow(e,2)*math.pow(math.sin(fp),2);
	R1 = a*e1a/math.pow(1-R2,1.5);
	
	N2 = math.pow(e,2)*math.pow(math.sin(fp),2);
	N1 = a/math.pow(1-N2,0.5);
	D = x0/(N1*k0);
	 
	# Latitude
	Q1 = N1 * math.tan(fp)/R1;
	Q2 = math.pow(D,2)/2;
	Q3 = (5 + 3*T1 + 10*C1-4*math.pow(C1,2)-9*e2)*math.pow(D,4)/24;
	Q4 = (61 + 90*T1 + 298*C1+45*math.pow(T1,2)-3*math.pow(C1,2)-252*e2)*math.pow(D,6)/720;
	# lat = (180/Math.PI)*(fp - Q1*(Q2 - Q3 + Q4)); # angle is in radian jezz
	lat = math.degrees(fp - Q1*(Q2 - Q3 + Q4)); # angle is in radian jezz
	
	# Longitude 
	Q5 = D;
	Q6 = (1 + 2*T1 + C1) * math.pow(D,3)/6;
	Q7 = (5-2*C1+28*T1-3*math.pow(C1,2) + 8 * e1sq + 24 * math.pow(T1,2))*math.pow(D,5)/120;
	
	longi = longi0 - math.degrees((Q5 - Q6 + Q7)/math.cos(fp));
	
	print("Latitude: %10.10f " %(lat));
	print("Longitude: %10.10f " %(longi));
	return (lat, longi)