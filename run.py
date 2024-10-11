import mysql.connector
from geopy.distance import geodesic

connection = mysql.connector.connect(
    host="localhost",
    database="flight_game",
    user="nirajan",
    password="pass_word"
)


oihoihihlihl

print(connection, "connection established")


# For airport location in the game
def airport_type():
    db = """SELECT 
                airport.ident, 
                airport.name, 
                airport.iso_country, 
                country.continent, 
                airport.latitude_deg, 
                airport.longitude_deg, 
                country.name AS country_name
            FROM 
                airport
            JOIN 
                country ON airport.iso_country = country.iso_country
            WHERE 
                airport.type = 'large_airport' 
            GROUP BY 
                airport.iso_country
            ORDER BY 
                country.continent;"""

    db_cursor = connection.cursor(dictionary=True)
    db_cursor.execute(db)
    result = db_cursor.fetchall()
    return result


# Get airport information
def get_airport_info(ident):
    db = """SELECT 
                airport.ident, 
                airport.name AS airport_name, 
                airport.iso_country, 
                country.name AS country_name,
                airport.continent,
                airport.latitude_deg,
                airport.longitude_deg  
            FROM airport 
            JOIN country ON airport.iso_country = country.iso_country
            WHERE airport.ident = %s"""

    db_cursor = connection.cursor(dictionary=True)
    db_cursor.execute(db, (ident,))
    result = db_cursor.fetchone()
    return result


# To calculate distance between airports in the game
def calculate_distance(current, next):
    start = get_airport_info(current)
    end = get_airport_info(next)
    return geodesic((start['latitude_deg'], start['longitude_deg']),
                    (end['latitude_deg'], end['longitude_deg'])).km


# To get airports in range
def airport_in_range(icao, airports_range, distance_range):
    travel_range = []
    for airport in airports_range:
        distance = calculate_distance(icao, airport['ident'])
        if distance <= distance_range and distance != 0:
            travel_range.append(airport)
    return travel_range


def update_visited_location(destination_info):
    # Insert or update the location based on the ident (unique identifier)
    db = '''INSERT INTO flight_game.visited_locations (ident, airport_name, continent, country) 
            VALUES (%s, %s, %s, %s)
            ;'''
    db_cursor = connection.cursor()
    db_cursor.execute(db, (destination_info['ident'], destination_info['airport_name'],
                           destination_info['continent'], destination_info['country_name']))
    connection.commit()

# Goal check using the in-memory data structure
def check_goal():
    db = """SELECT continent, COUNT(DISTINCT country) AS country_count
            FROM visited_locations
            GROUP BY continent
            HAVING country_count >= 2;"""

    db_cursor = connection.cursor()
    db_cursor.execute(db)
    results = db_cursor.fetchall()

    visited_continents = len(results)

    if visited_continents == 5:
        print("You have won the game! You have visited at least 2 countries in 5 continents.")
        for result in results:
            print(f"Continent: {result[0]}, Number of distinct countries: {result[1]}")
            break
    else:
        print(f"You have visited {visited_continents} continents with at least 2 countries. Keep exploring!")


def check_visited_locations(visited_goals):
    print("You have visited the following continents and countries:")
    for continent, countries in visited_goals.items():
        print(f"Continent: {continent}, Countries: {', '.join(countries)}")

# Main game function
def main():
    print("WELCOME TO THE ECO TRAVEL CHALLENGE")
    player_name = input("Enter your name: ")

    money = 2000
    distance_range = 10000
    allocated_co2 = 8000

    all_airports = airport_type()

    # Initialize visited goals
    visited_goals = {}

    for airport in all_airports:
        print(
            f"{airport['name']}, ICAO: {airport['ident']}, Country: {airport['country_name']}, Continent: {airport['continent']}")

    current_airport = input("Enter ICAO code to start the game: ")

    while True:
        airport = get_airport_info(current_airport)
        print(f"You are at {airport['airport_name']}, {airport['country_name']}, {airport['continent']}.")
        print(
            f"You have \nMONEY: €{money:.0f} \nRANGE: {distance_range:.0f} km \nALLOCATED CO2: {allocated_co2:.0f} kg")

        if money > 0:
            question_fuel = input("Do you want to buy fuel? (y/n): ").upper()

            if question_fuel == "Y":
                question_cost = input("Enter amount to spend on fuel (€1 = 2km): ")
                question_cost = int(question_cost)

                if question_cost > money:
                    print("Not enough money.")
                else:
                    money -= question_cost
                    distance_range += question_cost * 2
                    print(
                        f"You have: \nMONEY: €{money:.0f} \nRANGE: {distance_range:.0f} km \nALLOCATED CO2: {allocated_co2:.0f} kg")

            elif question_fuel == "N":
                print("You chose not to buy fuel.")
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

        # Get available airports in range
        airport1 = airport_in_range(current_airport, all_airports, distance_range)
        print(f"There are {len(airport1)} airports in range:")
        if len(airport1) == 0:
            print('You are out of range. Game over.')
            break
        else:
            for airport in airport1:
                ap_distance = calculate_distance(current_airport, airport['ident'])
                co2_cost = ap_distance * 0.4
                print(
                    f"{airport['name']}, ICAO: {airport['ident']}, continent: {airport['continent']}, Country: {airport['country_name']}, Distance: {ap_distance:.0f} km, CO2 Cost: {co2_cost:.0f} kg")

            destination = input("Enter destination ICAO code: ")
            selected_distance = calculate_distance(current_airport, destination)
            co2_cost = selected_distance * 0.4

            if co2_cost > allocated_co2:
                print("You cannot travel to this airport as it exceeds your CO2 allocation. Game over.")
                break

            distance_range -= selected_distance
            allocated_co2 -= co2_cost
            destination_info = get_airport_info(destination)



            update_visited_location(destination_info)



            #to exit game
            db = """SELECT continent, COUNT(DISTINCT country) AS country_count
                                FROM visited_locations
                                GROUP BY continent
                                HAVING country_count >= 2;"""

            db_cursor = connection.cursor()
            db_cursor.execute(db)
            results = db_cursor.fetchall()
            visited_continents = len(results)

            if visited_continents == 5:
                print("Congratulations! You have won the game!")
                break  # Exit the game once the goal is fulfilled

            check_goal()

            current_airport = destination


# Run the game
main()
