from utils.distance import calculate_distance_miles
def test_same_coordinates_are_zero():assert calculate_distance_miles(35.2271,-80.8431,35.2271,-80.8431)==0
def test_known_approximate_distance():assert 5<calculate_distance_miles(35.2271,-80.8431,35.289,-80.893)<6
