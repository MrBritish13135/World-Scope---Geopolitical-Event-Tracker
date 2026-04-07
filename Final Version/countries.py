# countries.py
# Official country names used by the GeoPandas 'naturalearth_lowres' dataset.
#
# BUG FIX: "United States of America" was already correct here, but the
#           database.py sample data was using "USA" — that mismatch has been
#           corrected in database.py (populate_sample_data).
#
# NOTE: These names must match GeoPandas exactly for the heat-map to colour
#       the correct country.  If you add a new country and the map won't shade
#       it, check the spelling against the 'NAME' column in the shapefile.
#       Common aliases are handled in dashboard.py → draw_world_map().

VALID_COUNTRIES: list[str] = sorted([
    "Afghanistan", "Angola", "Albania", "United Arab Emirates", "Argentina",
    "Armenia", "Antarctica", "Australia", "Azerbaijan", "Burundi", "Belgium",
    "Benin", "Burkina Faso", "Bangladesh", "Bulgaria", "Belarus", "Belize",
    "Bolivia", "Brazil", "Brunei", "Bhutan", "Botswana", "Central African Rep.",
    "Canada", "Switzerland", "Chile", "China", "Ivory Coast", "Cameroon",
    "Dem. Rep. Congo", "Congo", "Colombia", "Costa Rica", "Cuba", "Cyprus",
    "Czech Rep.", "Germany", "Djibouti", "Denmark", "Dominican Rep.", "Algeria",
    "Ecuador", "Egypt", "Eritrea", "Spain", "Estonia", "Ethiopia", "Finland",
    "Fiji", "Falkland Is.", "France", "Gabon", "United Kingdom", "Georgia",
    "Ghana", "Guinea", "Gambia", "Guinea-Bissau", "Eq. Guinea", "Greece",
    "Greenland", "Guatemala", "Guyana", "Honduras", "Croatia", "Haiti", "Hungary",
    "Indonesia", "India", "Ireland", "Iran", "Iraq", "Iceland", "Israel", "Italy",
    "Jamaica", "Jordan", "Japan", "Kazakhstan", "Kenya", "Kyrgyzstan", "Cambodia",
    "South Korea", "Kuwait", "Laos", "Lebanon", "Liberia", "Libya", "Sri Lanka",
    "Lesotho", "Lithuania", "Luxembourg", "Latvia", "Morocco", "Moldova",
    "Madagascar", "Mexico", "Macedonia", "Mali", "Myanmar", "Montenegro",
    "Mongolia", "Mozambique", "Mauritania", "Malawi", "Malaysia", "Namibia",
    "New Caledonia", "Niger", "Nigeria", "Nicaragua", "Netherlands", "Norway",
    "Nepal", "New Zealand", "Oman", "Pakistan", "Panama", "Peru", "Philippines",
    "Papua New Guinea", "Poland", "Puerto Rico", "North Korea", "Portugal",
    "Paraguay", "Qatar", "Romania", "Russia", "Rwanda", "W. Sahara", "Saudi Arabia",
    "Sudan", "S. Sudan", "Senegal", "Solomon Is.", "Sierra Leone", "El Salvador",
    "Somaliland", "Somalia", "Serbia", "Suriname", "Slovakia", "Slovenia",
    "Sweden", "Swaziland", "Syria", "Chad", "Togo", "Thailand", "Tajikistan",
    "Turkmenistan", "Timor-Leste", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Taiwan", "Tanzania", "Uganda", "Ukraine", "Uruguay", "United States of America",
    "Uzbekistan", "Venezuela", "Vietnam", "Vanuatu", "Yemen", "South Africa",
    "Zambia", "Zimbabwe"
])