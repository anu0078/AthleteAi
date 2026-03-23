import os
import re
import json
from google import genai
from dotenv import load_dotenv
 
load_dotenv()

SPORTS_HINDI = {
    'wrestling':'कुश्ती','kabaddi':'कबड्डी','athletics':'एथलेटिक्स','boxing':'मुक्केबाजी',
    'football':'फुटबॉल','cricket':'क्रिकेट','volleyball':'वॉलीबॉल','badminton':'बैडमिंटन',
    'hockey':'हॉकी','kho_kho':'खो-खो','weightlifting':'भारोत्तोलन','archery':'तीरंदाजी',
    'judo':'जूडो','swimming':'तैराकी',
}
SPORTS_EN = {
    'wrestling':'Wrestling','kabaddi':'Kabaddi','athletics':'Athletics','boxing':'Boxing',
    'football':'Football','cricket':'Cricket','volleyball':'Volleyball','badminton':'Badminton',
    'hockey':'Hockey','kho_kho':'Kho-Kho','weightlifting':'Weightlifting','archery':'Archery',
    'judo':'Judo','swimming':'Swimming',
}
LEVEL_DESCRIPTION = {
    'beginner':'just starting out (0-6 months experience)',
    'intermediate':'training regularly for 6-18 months',
    'advanced':'competitive athlete with 2+ years of training',
}
SPORT_ICONS = {
    'wrestling':'🤼','kabaddi':'🏃','athletics':'🏃','boxing':'🥊','football':'⚽',
    'cricket':'🏏','volleyball':'🏐','badminton':'🏸','hockey':'🏑','kho_kho':'🏃',
    'weightlifting':'🏋️','archery':'🎯','judo':'🥋','swimming':'🏊',
}


# ── Sport-specific fallback data (used if AI fails) ───────────────────────────

FALLBACK_EXERCISES = {
    'wrestling': [
        {"icon":"🤼","name":"Sprawl Drill","detail":"Stand, shoot hips back fast, sprawl flat on ground, push up. Repeat explosively.","tags":["Hip Power","No Equipment"],"sets":"4x12"},
        {"icon":"🦵","name":"Hindu Squats","detail":"Hands forward, squat deep, rise on toes at bottom. Continuous flowing motion.","tags":["Legs","No Equipment"],"sets":"4x20"},
        {"icon":"💪","name":"Wrestler's Bridge","detail":"Lie on back, arch up onto forehead and feet. Hold and rock forward-back.","tags":["Neck","No Equipment"],"sets":"3x30sec"},
        {"icon":"🏃","name":"Bear Crawl","detail":"On all fours, crawl forward 10m then backward 10m. Keep hips low.","tags":["Full Body","No Equipment"],"sets":"4x20m"},
    ],
    'badminton': [
        {"icon":"🏸","name":"Shadow Footwork","detail":"Imagine court, move to 6 corners repeatedly. Stay on toes, fast steps.","tags":["Footwork","No Equipment"],"sets":"4x90sec"},
        {"icon":"💨","name":"Wrist Rotation","detail":"Hold a water bottle, rotate wrist in full circles — forward and backward.","tags":["Wrist","Water Bottle"],"sets":"3x20 each"},
        {"icon":"🦵","name":"Split Step Jumps","detail":"Jump and land with feet wide apart, immediately jump back together. Fast rhythm.","tags":["Agility","No Equipment"],"sets":"4x15"},
        {"icon":"🏃","name":"Lateral Shuffles","detail":"Shuffle sideways 5 steps left, 5 steps right. Stay low, don't cross feet.","tags":["Speed","No Equipment"],"sets":"4x60sec"},
    ],
    'boxing': [
        {"icon":"🥊","name":"Shadow Boxing","detail":"3-minute rounds: jab, cross, hook, uppercut combinations. Stay light on feet.","tags":["Technique","No Equipment"],"sets":"4x3min"},
        {"icon":"💪","name":"Push-up Variations","detail":"Standard, wide, diamond push-ups in sequence. 10 of each without stopping.","tags":["Upper Body","No Equipment"],"sets":"4x30"},
        {"icon":"🏃","name":"High Knees","detail":"Run in place, drive knees above waist. Pump arms like boxing guard.","tags":["Cardio","No Equipment"],"sets":"4x60sec"},
        {"icon":"🦵","name":"Squat to Uppercut","detail":"Squat down, explode up throwing double uppercut. Power from legs.","tags":["Power","No Equipment"],"sets":"4x15"},
    ],
    'athletics': [
        {"icon":"🏃","name":"Stair Sprints","detail":"Sprint up stairs or slope, walk down. Full effort going up.","tags":["Speed","Stairs"],"sets":"8x30sec"},
        {"icon":"🦵","name":"Bounding","detail":"Exaggerated running strides — push off hard, reach far with each step.","tags":["Power","No Equipment"],"sets":"4x20m"},
        {"icon":"💪","name":"Core Planks","detail":"Hold plank on forearms. Keep body straight as a board.","tags":["Core","No Equipment"],"sets":"4x45sec"},
        {"icon":"🏃","name":"Ankle Hops","detail":"Small fast hops on both feet. Minimal knee bend, spring from ankles.","tags":["Plyometric","No Equipment"],"sets":"4x30"},
    ],
    'kabaddi': [
        {"icon":"🏃","name":"Raider Sprints","detail":"Sprint 10m, touch ground, sprint back. Simulate raiding in and out.","tags":["Speed","No Equipment"],"sets":"6x10m"},
        {"icon":"🦵","name":"Thigh Slap Squats","detail":"Deep squat, slap both thighs at bottom, explode up. Build raiding power.","tags":["Legs","No Equipment"],"sets":"4x15"},
        {"icon":"💨","name":"Cant Practice","detail":"Repeat 'kabaddi kabaddi' while doing 20 steps — train breath control.","tags":["Breathing","No Equipment"],"sets":"5x20steps"},
        {"icon":"💪","name":"Tackle Hold","detail":"Hold a tree or pole, pull as hard as possible for 10 seconds.","tags":["Grip","Pole/Tree"],"sets":"4x10sec"},
    ],
    'cricket': [
        {"icon":"🏏","name":"Batting Stance Squats","detail":"Take batting stance, do slow squat. Stay balanced, head level.","tags":["Balance","No Equipment"],"sets":"4x15"},
        {"icon":"💪","name":"Bowling Action Drill","detail":"Full bowling run-up and action without ball. Focus on hip rotation.","tags":["Technique","No Equipment"],"sets":"4x10"},
        {"icon":"🏃","name":"Running Between Wickets","detail":"Sprint 22 yards, turn and sprint back. Simulate quick singles.","tags":["Speed","No Equipment"],"sets":"8x22m"},
        {"icon":"🎯","name":"Wall Catch","detail":"Throw a ball against wall at angles, catch with one hand. Vary height.","tags":["Catching","Wall+Ball"],"sets":"3x2min"},
    ],
    'football': [
        {"icon":"⚽","name":"Dribbling Cones","detail":"Use stones or bottles as cones, dribble through with both feet.","tags":["Technique","Stones/Bottles"],"sets":"4x2min"},
        {"icon":"🦵","name":"Jump Squats","detail":"Squat down, explode up as high as possible. Land softly, repeat.","tags":["Jumping","No Equipment"],"sets":"4x15"},
        {"icon":"🏃","name":"Shuttle Runs","detail":"5m-10m-15m shuttle. Sprint, touch ground at each line, sprint back.","tags":["Agility","No Equipment"],"sets":"5x3lines"},
        {"icon":"💪","name":"Wall Passes","detail":"Pass ball against wall with inside of foot, control return, pass again.","tags":["Passing","Wall+Ball"],"sets":"3x3min"},
    ],
    'hockey': [
        {"icon":"🏑","name":"Stick Handling Drill","detail":"Dribble ball in figure-8 pattern around two stones.","tags":["Technique","Stick+Ball"],"sets":"4x2min"},
        {"icon":"🦵","name":"Low Squat Walk","detail":"Stay in deep squat, walk forward 10m. Builds hockey position strength.","tags":["Legs","No Equipment"],"sets":"4x10m"},
        {"icon":"🏃","name":"Lateral Speed Ladder","detail":"Draw lines on ground 1ft apart, run sideways through them fast.","tags":["Footwork","No Equipment"],"sets":"4x60sec"},
        {"icon":"💪","name":"Push Pass Practice","detail":"Push ball against wall, receive and push again. Quick hands.","tags":["Passing","Wall+Ball"],"sets":"3x3min"},
    ],
    'weightlifting': [
        {"icon":"🏋️","name":"Overhead Press with Bricks","detail":"Hold two bricks, press overhead fully. Control the descent slowly.","tags":["Shoulders","Bricks"],"sets":"4x12"},
        {"icon":"🦵","name":"Pause Squats","detail":"Squat down, pause 3 seconds at bottom, drive up explosively.","tags":["Legs","No Equipment"],"sets":"4x10"},
        {"icon":"💪","name":"Isometric Pull","detail":"Tie rope to a tree, pull as hard as possible for 8 seconds.","tags":["Back","Rope+Tree"],"sets":"4x8sec"},
        {"icon":"🏃","name":"Heavy Bag Deadlift","detail":"Lift heaviest bag from ground to hip height. Use hip hinge.","tags":["Full Body","Heavy Bag"],"sets":"4x8"},
    ],
    'archery': [
        {"icon":"🎯","name":"Bow Arm Hold","detail":"Extend arm forward, hold 1kg water bottle for 60 seconds.","tags":["Shoulder","Water Bottle"],"sets":"4x60sec"},
        {"icon":"💪","name":"Towel Pull-Apart","detail":"Stretch towel between hands, pull apart at chest height. Hold 2 sec.","tags":["Back","Towel"],"sets":"4x15"},
        {"icon":"🧘","name":"Single Leg Stand","detail":"Stand on one leg with eyes closed for 30 seconds. Switch legs.","tags":["Balance","No Equipment"],"sets":"4x30sec"},
        {"icon":"🎯","name":"Draw Simulation","detail":"Mime full draw motion slowly, hold at full draw for 5 seconds.","tags":["Technique","No Equipment"],"sets":"4x10"},
    ],
    'judo': [
        {"icon":"🥋","name":"Uchi Komi Entry Drill","detail":"Practise throw entry against wall — step in, turn, hip load.","tags":["Technique","No Equipment"],"sets":"5x20"},
        {"icon":"💪","name":"Towel Pull-ups","detail":"Throw towel over strong branch, grip both ends, pull yourself up.","tags":["Grip","Towel+Branch"],"sets":"4x8"},
        {"icon":"🦵","name":"Sumo Squat Hold","detail":"Wide stance squat, hold at 90 degrees. Builds unbalancing strength.","tags":["Legs","No Equipment"],"sets":"4x45sec"},
        {"icon":"🏃","name":"Breakfall Practice","detail":"From standing, do controlled forward and backward rolls on grass.","tags":["Ukemi","No Equipment"],"sets":"4x10"},
    ],
    'swimming': [
        {"icon":"🏊","name":"Dryland Freestyle Arms","detail":"Bend forward 90°, rotate arms in full freestyle stroke motion.","tags":["Technique","No Equipment"],"sets":"4x60sec"},
        {"icon":"💪","name":"Superman Hold","detail":"Lie face down, lift arms and legs simultaneously. Hold position.","tags":["Back","No Equipment"],"sets":"4x30sec"},
        {"icon":"🦵","name":"Flutter Kicks","detail":"Lie on back, lift legs 6 inches, do small fast kicks.","tags":["Core+Legs","No Equipment"],"sets":"4x45sec"},
        {"icon":"🏃","name":"Resistance Rope Pulls","detail":"Tie rope to door/tree, pull with straight arms overhead to hips.","tags":["Lats","Rope"],"sets":"4x15"},
    ],
    'volleyball': [
        {"icon":"🏐","name":"Spike Jump Drill","detail":"Jump and reach as high as possible, snap wrist at top. Land softly.","tags":["Jumping","No Equipment"],"sets":"4x15"},
        {"icon":"💪","name":"Wall Setting","detail":"Set ball against wall repeatedly — fingertip control, quick wrists.","tags":["Technique","Wall+Ball"],"sets":"4x2min"},
        {"icon":"🦵","name":"Broad Jumps","detail":"Jump forward as far as possible, land both feet together.","tags":["Power","No Equipment"],"sets":"4x10"},
        {"icon":"🏃","name":"Defensive Shuffle","detail":"Low stance, shuffle left 3 steps, dive forward, recover. Repeat.","tags":["Defense","No Equipment"],"sets":"4x60sec"},
    ],
}

FALLBACK_NUTRITION = {
    'wrestling':    {"daily_cost_range":"Rs.90-130","tags":["High Protein","100% Indian Foods"],"meals":[{"time":"5:30 AM","type":"Wake-up","name":"Turmeric Milk","cost":"Rs.8","items":["Warm milk","Turmeric","Pinch of salt"],"highlight":["Warm milk"]},{"time":"7:00 AM","type":"Breakfast","name":"Egg Roti","cost":"Rs.25","items":["3 boiled eggs","2 roti","Banana"],"highlight":["3 boiled eggs","Banana"]},{"time":"10:30 AM","type":"Snack","name":"Peanut Chaat","cost":"Rs.10","items":["Roasted peanuts","Onion","Lemon"],"highlight":["Roasted peanuts"]},{"time":"1:00 PM","type":"Lunch","name":"Rajma Chawal","cost":"Rs.30","items":["Rice","Rajma","Sabzi","Curd"],"highlight":["Rajma","Curd"]},{"time":"3:30 PM","type":"Pre-Training","name":"Sattu Shake","cost":"Rs.12","items":["Sattu","Banana","Water","Salt"],"highlight":["Sattu","Banana"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Roti","cost":"Rs.20","items":["2 eggs","2 roti","Onion"],"highlight":["2 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Roti + Milk","cost":"Rs.18","items":["Dal","Roti","Warm milk"],"highlight":["Warm milk"]}],"avoid":["Cold drinks","Fried food","Maida"],"hydration":"4-5 litres per day","natural_supplements":["Peanuts 50g daily","Banana pre-training","Turmeric milk for recovery"]},
    'badminton':    {"daily_cost_range":"Rs.80-110","tags":["Light & Fast","100% Indian Foods"],"meals":[{"time":"6:00 AM","type":"Wake-up","name":"Lemon Honey Water","cost":"Rs.3","items":["Warm water","Lemon","Honey"],"highlight":["Lemon"]},{"time":"7:30 AM","type":"Breakfast","name":"Poha + Banana","cost":"Rs.15","items":["Poha","Peanuts","Banana"],"highlight":["Peanuts","Banana"]},{"time":"11:00 AM","type":"Snack","name":"Curd Rice","cost":"Rs.12","items":["Curd","Rice","Salt"],"highlight":["Curd"]},{"time":"1:30 PM","type":"Lunch","name":"Roti Dal Sabzi","cost":"Rs.25","items":["2 roti","Moong dal","Sabzi"],"highlight":["Moong dal"]},{"time":"4:00 PM","type":"Pre-Training","name":"Banana + Peanuts","cost":"Rs.10","items":["Banana","Roasted peanuts"],"highlight":["Banana","Roasted peanuts"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Bhurji Roti","cost":"Rs.22","items":["2 eggs","2 roti","Tomato"],"highlight":["2 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Roti Milk","cost":"Rs.18","items":["Dal","Roti","Warm milk"],"highlight":["Warm milk"]}],"avoid":["Heavy food before training","Cold drinks"],"hydration":"3-4 litres per day","natural_supplements":["Banana 30 min before training","Coconut water after matches"]},
    'boxing':       {"daily_cost_range":"Rs.90-130","tags":["High Protein","Power Foods"],"meals":[{"time":"5:30 AM","type":"Wake-up","name":"Warm Lemon Water","cost":"Rs.2","items":["Warm water","Lemon","Salt"],"highlight":["Lemon"]},{"time":"7:00 AM","type":"Breakfast","name":"Egg Paratha","cost":"Rs.22","items":["2 egg parathas","Curd","Banana"],"highlight":["2 egg parathas","Banana"]},{"time":"10:30 AM","type":"Snack","name":"Chana Chaat","cost":"Rs.10","items":["Boiled chana","Onion","Lemon"],"highlight":["Boiled chana"]},{"time":"1:00 PM","type":"Lunch","name":"Dal Rice Sabzi","cost":"Rs.30","items":["Rice","Dal","Sabzi","Salad"],"highlight":["Dal"]},{"time":"3:30 PM","type":"Pre-Training","name":"Banana Milk","cost":"Rs.15","items":["Banana","Milk"],"highlight":["Banana","Milk"]},{"time":"7:30 PM","type":"Post-Training","name":"Egg Bhurji","cost":"Rs.20","items":["3 eggs","Roti","Onion"],"highlight":["3 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Roti","cost":"Rs.18","items":["Dal","2 roti","Sabzi"],"highlight":["Dal"]}],"avoid":["Alcohol","Processed food","Excess sugar"],"hydration":"4-5 litres per day","natural_supplements":["Eggs daily for protein","Peanuts for healthy fats","Banana for quick energy"]},
    'athletics':    {"daily_cost_range":"Rs.80-120","tags":["High Carbs","Energy Foods"],"meals":[{"time":"5:30 AM","type":"Wake-up","name":"Banana + Water","cost":"Rs.5","items":["Banana","Warm water","Lemon"],"highlight":["Banana"]},{"time":"7:00 AM","type":"Breakfast","name":"Sattu Roti","cost":"Rs.18","items":["Sattu roti","Curd","Jaggery"],"highlight":["Sattu roti","Jaggery"]},{"time":"10:30 AM","type":"Snack","name":"Makhana Milk","cost":"Rs.15","items":["Roasted makhana","Warm milk"],"highlight":["Warm milk"]},{"time":"1:00 PM","type":"Lunch","name":"Rice Dal Sabzi","cost":"Rs.25","items":["Rice","Dal","Sabzi","Salad"],"highlight":["Rice","Dal"]},{"time":"3:30 PM","type":"Pre-Training","name":"Banana Dates","cost":"Rs.10","items":["Banana","2-3 dates","Water"],"highlight":["Banana","2-3 dates"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Roti Curd","cost":"Rs.22","items":["2 eggs","2 roti","Curd"],"highlight":["2 eggs","Curd"]},{"time":"9:30 PM","type":"Dinner","name":"Light Dal Roti","cost":"Rs.18","items":["Moong dal","Roti","Sabzi"],"highlight":["Moong dal"]}],"avoid":["Heavy food 2hrs before training","Cold drinks during training"],"hydration":"4-5 litres per day","natural_supplements":["Dates for quick energy","Banana pre-run","Sattu for sustained energy"]},
    'kabaddi':      {"daily_cost_range":"Rs.85-120","tags":["High Carbs + Protein","Indian Foods"],"meals":[{"time":"5:30 AM","type":"Wake-up","name":"Sattu Water","cost":"Rs.5","items":["Sattu","Water","Lemon","Salt"],"highlight":["Sattu"]},{"time":"7:00 AM","type":"Breakfast","name":"Roti Egg Sabzi","cost":"Rs.22","items":["2 roti","2 eggs","Sabzi"],"highlight":["2 eggs"]},{"time":"10:30 AM","type":"Snack","name":"Chana Jaggery","cost":"Rs.8","items":["Roasted chana","Jaggery"],"highlight":["Roasted chana","Jaggery"]},{"time":"1:00 PM","type":"Lunch","name":"Rice Rajma","cost":"Rs.28","items":["Rice","Rajma","Salad","Curd"],"highlight":["Rajma","Curd"]},{"time":"3:30 PM","type":"Pre-Training","name":"Banana Sattu","cost":"Rs.10","items":["Banana","Sattu","Water"],"highlight":["Banana","Sattu"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Roti","cost":"Rs.20","items":["2 eggs","2 roti"],"highlight":["2 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Roti Milk","cost":"Rs.18","items":["Dal","Roti","Warm milk"],"highlight":["Warm milk"]}],"avoid":["Cold drinks","Oily food before training"],"hydration":"4-5 litres per day","natural_supplements":["Sattu for stamina","Banana for raids energy","Jaggery for quick fuel"]},
    'cricket':      {"daily_cost_range":"Rs.80-120","tags":["Balanced Diet","100% Indian Foods"],"meals":[{"time":"6:00 AM","type":"Wake-up","name":"Lemon Water","cost":"Rs.2","items":["Warm water","Lemon","Honey"],"highlight":["Lemon"]},{"time":"7:30 AM","type":"Breakfast","name":"Poha + Eggs","cost":"Rs.20","items":["Poha","2 boiled eggs","Banana"],"highlight":["2 boiled eggs","Banana"]},{"time":"11:00 AM","type":"Snack","name":"Peanut Chikki","cost":"Rs.8","items":["Peanut chikki","Water"],"highlight":["Peanut chikki"]},{"time":"1:00 PM","type":"Lunch","name":"Roti Dal Sabzi","cost":"Rs.25","items":["3 roti","Dal","Sabzi","Curd"],"highlight":["Dal","Curd"]},{"time":"3:30 PM","type":"Pre-Match","name":"Banana + Dates","cost":"Rs.10","items":["Banana","2 dates","Water"],"highlight":["Banana","2 dates"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Roti","cost":"Rs.20","items":["2 eggs","2 roti","Sabzi"],"highlight":["2 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Chawal","cost":"Rs.20","items":["Rice","Dal","Sabzi"],"highlight":["Dal"]}],"avoid":["Heavy food on match day","Cold drinks in sun"],"hydration":"4-5 litres per day","natural_supplements":["Banana between innings","Dates for quick energy","Coconut water in field"]},
    'football':     {"daily_cost_range":"Rs.85-120","tags":["High Carbs","Endurance Foods"],"meals":[{"time":"6:00 AM","type":"Wake-up","name":"Warm Lemon Water","cost":"Rs.2","items":["Warm water","Lemon","Salt"],"highlight":["Lemon"]},{"time":"7:30 AM","type":"Breakfast","name":"Banana Roti Egg","cost":"Rs.22","items":["2 roti","2 eggs","Banana"],"highlight":["2 eggs","Banana"]},{"time":"11:00 AM","type":"Snack","name":"Sattu Drink","cost":"Rs.8","items":["Sattu","Water","Lemon","Salt"],"highlight":["Sattu"]},{"time":"1:00 PM","type":"Lunch","name":"Rice Dal Sabzi","cost":"Rs.35","items":["Rice","Dal","Sabzi","Curd"],"highlight":["Rice","Curd"]},{"time":"3:30 PM","type":"Pre-Training","name":"Banana + Peanuts","cost":"Rs.10","items":["Banana","Peanuts"],"highlight":["Banana","Peanuts"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Roti","cost":"Rs.20","items":["2 eggs","2 roti","Sabzi"],"highlight":["2 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Roti Milk","cost":"Rs.18","items":["Dal","Roti","Warm milk"],"highlight":["Dal","Warm milk"]}],"avoid":["Heavy meals 3hrs before training","Cold drinks during play"],"hydration":"5-6 litres per day","natural_supplements":["Banana pre-training","Sattu for stamina","ORS after intense sessions"]},
}

DEFAULT_NUTRITION = {"daily_cost_range":"Rs.80-120","tags":["100% Indian Foods","Athlete Optimised"],"meals":[{"time":"5:30 AM","type":"Wake-up","name":"Warm Lemon Water","cost":"Rs.2","items":["Warm water","Lemon","Pinch of salt"],"highlight":["Lemon"]},{"time":"7:00 AM","type":"Breakfast","name":"Egg Roti + Banana","cost":"Rs.22","items":["2 boiled eggs","2 roti","Banana"],"highlight":["2 boiled eggs","Banana"]},{"time":"10:30 AM","type":"Snack","name":"Peanut Chaat","cost":"Rs.10","items":["Roasted peanuts","Lemon","Onion"],"highlight":["Roasted peanuts"]},{"time":"1:00 PM","type":"Lunch","name":"Dal Chawal Sabzi","cost":"Rs.28","items":["Rice","Dal","Sabzi","Curd"],"highlight":["Dal","Curd"]},{"time":"3:30 PM","type":"Pre-Training","name":"Banana + Sattu","cost":"Rs.12","items":["Banana","Sattu","Water","Salt"],"highlight":["Banana","Sattu"]},{"time":"7:00 PM","type":"Post-Training","name":"Egg Roti","cost":"Rs.20","items":["2 eggs","2 roti","Sabzi"],"highlight":["2 eggs"]},{"time":"9:30 PM","type":"Dinner","name":"Dal Roti + Milk","cost":"Rs.18","items":["Dal","Roti","Warm milk"],"highlight":["Warm milk"]}],"avoid":["Cold drinks","Fried food","Maida products"],"hydration":"3-4 litres per day","natural_supplements":["Peanuts 50g daily for protein","Banana before training","Turmeric milk at night for recovery"]}

def _build_fallback_workout(sport, level, gender='male'):
    sport_name = SPORTS_EN.get(sport, sport.title())

    # 50 unique exercises split across 5 training days (10 each day)
    # Each list = one day's focus
    ALL_DAY_EXERCISES = {
        'wrestling': {
            'mon': [  # Strength
                {"icon":"🤼","name":"Sprawl Drill","detail":"Stand, shoot hips back explosively, sprawl flat, push up. Repeat.","benefit":"Builds defensive sprawl reflex — most important wrestling survival skill.","tags":["Hip Power","No Equipment"],"sets":"4x12"},
                {"icon":"🦵","name":"Hindu Squats","detail":"Hands forward, squat deep, rise on toes at bottom. Continuous motion.","benefit":"Builds knee drive and leg endurance for repeated takedown attempts.","tags":["Legs","No Equipment"],"sets":"4x20"},
                {"icon":"💪","name":"Wrestler's Bridge","detail":"Lie on back, arch up onto forehead and feet. Rock forward-back.","benefit":"Strengthens neck — critical for resisting pins and maintaining position.","tags":["Neck","No Equipment"],"sets":"3x30sec"},
                {"icon":"🏃","name":"Bear Crawl","detail":"All fours, crawl forward 10m then backward 10m. Keep hips low.","benefit":"Mimics wrestling stance movement — builds full-body coordination.","tags":["Full Body","No Equipment"],"sets":"4x20m"},
                {"icon":"💪","name":"Push-up to Hip Escape","detail":"Do push-up, then immediately shrimp backward along ground. Repeat.","benefit":"Combines upper body strength with ground escape movement pattern.","tags":["Upper Body","No Equipment"],"sets":"4x10"},
                {"icon":"🦵","name":"Pistol Squat Hold","detail":"Stand on one leg, extend other forward, lower slowly. Hold at bottom.","benefit":"Single-leg strength for shooting takedowns and maintaining stance.","tags":["Balance","No Equipment"],"sets":"3x8 each"},
                {"icon":"🏃","name":"Frog Jumps","detail":"Deep squat, jump forward as far as possible, land in squat. Repeat.","benefit":"Explosive leg power for shooting double-leg takedowns.","tags":["Power","No Equipment"],"sets":"4x10"},
                {"icon":"💪","name":"Isometric Wall Push","detail":"Push both hands against wall as hard as possible for 10 seconds.","benefit":"Builds pushing strength used when breaking opponent's grip.","tags":["Chest","Wall"],"sets":"4x10sec"},
                {"icon":"🦵","name":"Reverse Lunge","detail":"Step backward into lunge, knee touches ground, drive back up.","benefit":"Hip flexor strength for penetration step in takedowns.","tags":["Legs","No Equipment"],"sets":"4x12 each"},
                {"icon":"🏃","name":"Ankle Circles + Hops","detail":"Rotate ankles 10 times, then hop on each foot 20 times.","benefit":"Ankle stability — prevents injury during scrambles.","tags":["Ankles","No Equipment"],"sets":"3x20"},
            ],
            'tue': [  # Speed & Agility
                {"icon":"🏃","name":"Level Change Drill","detail":"Stand, shoot in low to touch ground, explode back up. Repeat fast.","benefit":"Trains level change speed — key for finishing takedowns.","tags":["Speed","No Equipment"],"sets":"5x10"},
                {"icon":"🦵","name":"Lateral Bound","detail":"Jump sideways as far as possible, land on one foot, immediately jump back.","benefit":"Lateral explosiveness for circling and repositioning on mat.","tags":["Agility","No Equipment"],"sets":"4x10 each"},
                {"icon":"💪","name":"Explosive Push-ups","detail":"Push up explosively, hands leave ground at top. Land soft.","benefit":"Upper body explosiveness for lifting and throwing opponents.","tags":["Chest","No Equipment"],"sets":"4x10"},
                {"icon":"🏃","name":"High Knees Sprint","detail":"Run in place, knees above waist. Arms pump hard. 30 seconds max effort.","benefit":"Hip flexor speed for quicker penetration steps.","tags":["Cardio","No Equipment"],"sets":"5x30sec"},
                {"icon":"🦵","name":"Box Step Blast","detail":"Step up onto chair/step, drive opposite knee up, step back down fast.","benefit":"Single-leg explosive power for clearing to back.","tags":["Legs","Chair"],"sets":"4x12 each"},
                {"icon":"💪","name":"Rotational Throw Sim","detail":"Hold water bottle, rotate body explosively left then right. Fast hands.","benefit":"Rotational power for throws and bodylock attempts.","tags":["Core","Water Bottle"],"sets":"4x15 each"},
                {"icon":"🏃","name":"Reactive Sprawl","detail":"Standing, drop to sprawl position as fast as possible. Time yourself.","benefit":"Reaction time for defensive sprawls when opponent shoots.","tags":["Reaction","No Equipment"],"sets":"5x8"},
                {"icon":"🦵","name":"Side Shuffle + Drop","detail":"Shuffle 5 steps sideways, drop to one knee, stand. Repeat other side.","benefit":"Lateral movement and stance change speed.","tags":["Footwork","No Equipment"],"sets":"4x8 each"},
                {"icon":"💪","name":"Grip Crush","detail":"Squeeze a rolled-up towel or cloth as hard as possible. Hold 5 sec.","benefit":"Grip strength is everything in wrestling — controls opponent.","tags":["Grip","Towel"],"sets":"4x10"},
                {"icon":"🏃","name":"Burpee Variation","detail":"Drop to push-up, do push-up, jump up with hands overhead. Fast.","benefit":"Full-body conditioning — mirrors energy demands of a match.","tags":["Conditioning","No Equipment"],"sets":"4x10"},
            ],
            'thu': [  # Endurance
                {"icon":"🏃","name":"Match Simulation Run","detail":"Jog 2 min, sprint 30 sec, jog 2 min. Repeat 5 times.","benefit":"Mirrors the energy demands of a 6-minute wrestling match.","tags":["Cardio","No Equipment"],"sets":"5 rounds"},
                {"icon":"🦵","name":"Wall Sit","detail":"Back against wall, thighs parallel to floor. Hold as long as possible.","benefit":"Isometric leg endurance for maintaining stance during long matches.","tags":["Legs","Wall"],"sets":"4x60sec"},
                {"icon":"💪","name":"Plank Variations","detail":"Front plank 30sec, left side 30sec, right side 30sec. No rest between.","benefit":"Core endurance for maintaining tight body position throughout match.","tags":["Core","No Equipment"],"sets":"4 rounds"},
                {"icon":"🏃","name":"Stair Climb","detail":"Walk up stairs as fast as possible, walk down slowly. Repeat.","benefit":"Leg and cardiovascular endurance for sustained pressure wrestling.","tags":["Cardio","Stairs"],"sets":"10x climb"},
                {"icon":"🦵","name":"Squat Hold + Pulse","detail":"Hold deep squat for 20 sec, pulse up-down 2 inches for 20 sec.","benefit":"Slow-twitch muscle endurance for maintaining low wrestling stance.","tags":["Legs","No Equipment"],"sets":"4x40sec"},
                {"icon":"💪","name":"Dead Hang","detail":"Hang from tree branch, hold as long as possible.","benefit":"Grip and shoulder endurance for long clinch battles.","tags":["Grip","Branch"],"sets":"4x max hold"},
                {"icon":"🏃","name":"Shadow Wrestling","detail":"Full shadow wrestling movements for 3 minutes. Shots, sprawls, circles.","benefit":"Sport-specific endurance — trains the exact movements of wrestling.","tags":["Technique","No Equipment"],"sets":"4x3min"},
                {"icon":"🦵","name":"Step-ups Continuous","detail":"Step up and down on chair/step continuously for 2 minutes.","benefit":"Cardiovascular and leg endurance for continuous scramble situations.","tags":["Cardio","Chair"],"sets":"4x2min"},
                {"icon":"💪","name":"Superman Hold","detail":"Lie face down, lift arms and legs off ground. Hold.","benefit":"Lower back endurance for maintaining arched defensive position.","tags":["Back","No Equipment"],"sets":"4x30sec"},
                {"icon":"🏃","name":"Jumping Jacks","detail":"Classic jumping jacks. Maintain rhythm for full duration.","benefit":"Active recovery and cardiovascular base for match endurance.","tags":["Cardio","No Equipment"],"sets":"4x60sec"},
            ],
            'fri': [  # Technique
                {"icon":"🤼","name":"Double Leg Entry","detail":"From stance, penetration step, both hands inside knees, drive through.","benefit":"Practices the most fundamental offensive technique in wrestling.","tags":["Takedown","No Equipment"],"sets":"5x15"},
                {"icon":"🦵","name":"Stand-up Drill","detail":"From knees, base out, stand up quickly. Drop back to knees. Repeat.","benefit":"Escaping bottom position — trains referee's position stand-up.","tags":["Escape","No Equipment"],"sets":"4x15"},
                {"icon":"💪","name":"Hip Toss Sim","detail":"Stand, clasp hands, rotate and drive hips across. No partner needed.","benefit":"Hip positioning for throws — muscle memory for bodylock entry.","tags":["Throws","No Equipment"],"sets":"4x12 each"},
                {"icon":"🏃","name":"Penetration Step Drill","detail":"Drop lead knee to ground while driving forward. Alternate legs.","benefit":"The most important footwork in wrestling — closing distance.","tags":["Footwork","No Equipment"],"sets":"5x20"},
                {"icon":"🦵","name":"Shrimp (Hip Escape)","detail":"On back, bridge hips up, shoot hips sideways, reset. Alternate sides.","benefit":"Ground escape technique — used to recover guard or stand up.","tags":["Ground","No Equipment"],"sets":"4x10 each"},
                {"icon":"💪","name":"Granby Roll","detail":"On back, roll over shoulder, come up to base. Alternate shoulders.","benefit":"Rolling escape technique to avoid being pinned.","tags":["Ground","No Equipment"],"sets":"4x8 each"},
                {"icon":"🏃","name":"Snap Down Drill","detail":"Reach forward, snap hands down hard, drop opponent's level.","benefit":"Setting up takedowns by breaking opponent's posture.","tags":["Setup","No Equipment"],"sets":"4x15"},
                {"icon":"🦵","name":"Referee Position Hold","detail":"Get on all fours, hold perfect base position. Don't let anything collapse.","benefit":"Strong base position prevents being turned and scored on.","tags":["Position","No Equipment"],"sets":"4x45sec"},
                {"icon":"💪","name":"Underhook Battle Sim","detail":"Both arms fight for underhook position against door frame. Rotate.","benefit":"Upper body position battles — controls who dictates the match.","tags":["Clinch","Door Frame"],"sets":"4x30sec each"},
                {"icon":"🏃","name":"Circle Drill","detail":"In wrestler's stance, circle left 10 steps, right 10 steps. Stay low.","benefit":"Footwork and positioning — always stay at angle to opponent.","tags":["Footwork","No Equipment"],"sets":"4x60sec"},
            ],
            'sat': [  # Sport Drills
                {"icon":"🤼","name":"Full Match Shadow","detail":"6-minute shadow wrestling with full effort. Simulate entire match.","benefit":"Complete match simulation — builds mental and physical match fitness.","tags":["Match Sim","No Equipment"],"sets":"3x6min"},
                {"icon":"🦵","name":"Takedown Finish Drill","detail":"Practice completing takedown from knees position. Drive, lift, finish.","benefit":"Finishing strength — many wrestlers score takedowns but can't finish.","tags":["Finishing","No Equipment"],"sets":"4x10"},
                {"icon":"💪","name":"Wrist Control Drill","detail":"Control and rotate imaginary opponent's wrists. Fast hands.","benefit":"Wrist control sets up almost every wrestling technique.","tags":["Control","No Equipment"],"sets":"4x2min"},
                {"icon":"🏃","name":"Explosion Sprint","detail":"From crouch position, explode forward 10m. Walk back. Repeat.","benefit":"Starting explosion — first step speed in shooting takedowns.","tags":["Explosion","No Equipment"],"sets":"8x10m"},
                {"icon":"🦵","name":"Ankle Pick Sim","detail":"From stance, reach low, grab imaginary ankle, step around, finish.","benefit":"Ankle pick — high-percentage low-risk takedown technique.","tags":["Takedown","No Equipment"],"sets":"4x12 each"},
                {"icon":"💪","name":"Gut Wrench Sim","detail":"From knees, wrap arms around imaginary opponent, rotate side to side.","benefit":"Gut wrench scoring — turns opponent for back exposure points.","tags":["Turns","No Equipment"],"sets":"4x10 each"},
                {"icon":"🏃","name":"Level Change + Circle","detail":"Change levels (crouch to stand) while circling. Stay in stance.","benefit":"Multi-tasking movement — level change without losing position.","tags":["Movement","No Equipment"],"sets":"4x90sec"},
                {"icon":"🦵","name":"Sprawl + Base","detail":"Sprawl to stop shot, immediately base up to standing. Fast recovery.","benefit":"Complete defensive sequence — stop shot and recover position.","tags":["Defense","No Equipment"],"sets":"5x10"},
                {"icon":"💪","name":"Tie-up Battle","detail":"Clinch imaginary opponent, fight for collar tie and underhook. Move.","benefit":"Tie-up control determines who dictates offensive attacks.","tags":["Clinch","No Equipment"],"sets":"4x2min"},
                {"icon":"🏃","name":"Conditioning Finisher","detail":"30 sec max sprawls, 30 sec rest, 30 sec max shots. Repeat 4 times.","benefit":"Finishing conditioning — train when fatigued like end of match.","tags":["Conditioning","No Equipment"],"sets":"4 rounds"},
            ],
        },
    }

    # Generic 10-exercise day templates for sports not fully listed above
    GENERIC_DAYS = {
        'mon': [
            {"icon":"💪","name":"Push-ups","detail":"Standard push-ups. Full range of motion, chest to ground.","benefit":"Upper body pushing strength — used in almost every sport.","tags":["Chest","No Equipment"],"sets":"4x15"},
            {"icon":"🦵","name":"Jump Squats","detail":"Squat down, explode upward as high as possible. Land softly.","benefit":"Explosive leg power — the foundation of athletic performance.","tags":["Legs","No Equipment"],"sets":"4x15"},
            {"icon":"🏃","name":"Burpees","detail":"Drop to push-up, do push-up, jump up hands overhead.","benefit":"Full-body conditioning that mirrors sport-specific energy demands.","tags":["Full Body","No Equipment"],"sets":"4x10"},
            {"icon":"💪","name":"Diamond Push-ups","detail":"Hands close together forming diamond shape. Lower chest to hands.","benefit":"Tricep strength for pushing and extending movements.","tags":["Triceps","No Equipment"],"sets":"4x12"},
            {"icon":"🦵","name":"Lunges","detail":"Step forward, lower back knee to ground, drive back up. Alternate.","benefit":"Unilateral leg strength and balance for athletic movement.","tags":["Legs","No Equipment"],"sets":"4x12 each"},
            {"icon":"🏃","name":"Mountain Climbers","detail":"Plank position, drive knees to chest alternately. Fast pace.","benefit":"Core stability and hip flexor strength for dynamic movements.","tags":["Core","No Equipment"],"sets":"4x30sec"},
            {"icon":"💪","name":"Wide Push-ups","detail":"Hands wider than shoulder width. Lower chest between hands.","benefit":"Chest width and shoulder stability for contact sports.","tags":["Chest","No Equipment"],"sets":"4x12"},
            {"icon":"🦵","name":"Calf Raises","detail":"Stand on edge of step, raise and lower on toes. Full range.","benefit":"Calf strength and ankle stability — prevents common sports injuries.","tags":["Calves","Step"],"sets":"4x20"},
            {"icon":"🏃","name":"Plank Hold","detail":"Forearm plank. Keep hips level, breathe steadily.","benefit":"Core endurance for maintaining posture throughout competition.","tags":["Core","No Equipment"],"sets":"4x45sec"},
            {"icon":"💪","name":"Superman Hold","detail":"Lie face down, lift arms and legs simultaneously. Hold.","benefit":"Lower back strength for upright posture and injury prevention.","tags":["Back","No Equipment"],"sets":"4x30sec"},
        ],
        'tue': [
            {"icon":"🏃","name":"High Knees","detail":"Run in place, drive knees above waist. Fast arms.","benefit":"Hip flexor speed and cardiovascular conditioning.","tags":["Speed","No Equipment"],"sets":"5x30sec"},
            {"icon":"🦵","name":"Lateral Bounds","detail":"Jump sideways as far as possible, land one foot, bound back.","benefit":"Lateral explosive power for quick directional changes.","tags":["Agility","No Equipment"],"sets":"4x10 each"},
            {"icon":"💪","name":"Explosive Push-ups","detail":"Push up hard enough that hands leave ground at top.","benefit":"Upper body explosive power for contact and throwing.","tags":["Power","No Equipment"],"sets":"4x8"},
            {"icon":"🏃","name":"Shuttle Run","detail":"Sprint 5m, touch ground, sprint 10m, touch, sprint back. No rest.","benefit":"Change of direction speed — critical in all field sports.","tags":["Agility","No Equipment"],"sets":"5x3lines"},
            {"icon":"🦵","name":"Box Jump","detail":"Jump onto sturdy chair/step. Step down. Repeat.","benefit":"Lower body explosiveness and landing mechanics.","tags":["Power","Chair"],"sets":"4x10"},
            {"icon":"💪","name":"Clap Push-ups","detail":"Push up explosively, clap hands at top, land soft.","benefit":"Upper body explosive power and fast-twitch muscle activation.","tags":["Power","No Equipment"],"sets":"4x8"},
            {"icon":"🏃","name":"Suicide Sprints","detail":"Sprint to wall, back, double distance, back. Full effort.","benefit":"Sprint endurance and deceleration control.","tags":["Speed","No Equipment"],"sets":"5x2lines"},
            {"icon":"🦵","name":"Single-leg Hops","detail":"Hop forward on one leg 10 times. Switch. Land softly.","benefit":"Single-leg power and balance for sport-specific movements.","tags":["Balance","No Equipment"],"sets":"4x10 each"},
            {"icon":"💪","name":"Bear Crawl","detail":"On all fours, move forward 10m, backward 10m. Stay low.","benefit":"Full-body coordination and shoulder stability.","tags":["Full Body","No Equipment"],"sets":"4x20m"},
            {"icon":"🏃","name":"Jump Rope Simulation","detail":"Jump as if skipping rope — both feet, then alternate feet.","benefit":"Foot speed and coordination — foundation of all athletic footwork.","tags":["Footwork","No Equipment"],"sets":"4x60sec"},
        ],
        'thu': [
            {"icon":"🏃","name":"Long Distance Run","detail":"Run at comfortable pace for 15-20 minutes without stopping.","benefit":"Aerobic base — sustains energy levels during long competitions.","tags":["Cardio","No Equipment"],"sets":"1x20min"},
            {"icon":"🦵","name":"Wall Sit","detail":"Back against wall, thighs parallel to floor. Hold.","benefit":"Isometric leg endurance for maintaining athletic position.","tags":["Legs","Wall"],"sets":"4x60sec"},
            {"icon":"💪","name":"Plank Circuit","detail":"Front 30sec, right side 30sec, left side 30sec. No rest.","benefit":"360-degree core endurance for stable athletic performance.","tags":["Core","No Equipment"],"sets":"4 rounds"},
            {"icon":"🏃","name":"Stair Climbs","detail":"Walk up stairs as fast as possible, slow walk down.","benefit":"Cardiovascular and leg endurance for sustained performance.","tags":["Cardio","Stairs"],"sets":"10x climb"},
            {"icon":"🦵","name":"Squat Hold","detail":"Hold deep squat position. Breathe steadily. Don't rise.","benefit":"Leg endurance in low athletic stance.","tags":["Legs","No Equipment"],"sets":"4x60sec"},
            {"icon":"💪","name":"Dead Hang","detail":"Hang from branch or bar. Hold as long as possible.","benefit":"Grip and shoulder endurance for sustained holds.","tags":["Grip","Branch"],"sets":"4x max"},
            {"icon":"🏃","name":"Interval Walk-Run","detail":"Walk 1 min, run 2 min, walk 1 min. Repeat 6 times.","benefit":"Aerobic endurance with active recovery — sport-specific conditioning.","tags":["Cardio","No Equipment"],"sets":"6 rounds"},
            {"icon":"🦵","name":"Step-ups Continuous","detail":"Step up and down on chair for 2 full minutes.","benefit":"Cardiovascular and leg endurance combined.","tags":["Cardio","Chair"],"sets":"4x2min"},
            {"icon":"💪","name":"Towel Rows","detail":"Loop towel around tree, lean back, pull body to tree. Repeat.","benefit":"Back and bicep pulling strength for grip-based sports.","tags":["Back","Towel+Tree"],"sets":"4x12"},
            {"icon":"🏃","name":"Jumping Jacks","detail":"Classic jumping jacks. Maintain steady rhythm.","benefit":"Active recovery movement keeping heart rate elevated.","tags":["Cardio","No Equipment"],"sets":"4x60sec"},
        ],
        'fri': [
            {"icon":"🏅","name":"Sport Technique Drill","detail":"Practice the core movement of your sport for 3 minutes. Full focus.","benefit":"Muscle memory for sport-specific movement patterns.","tags":["Technique","No Equipment"],"sets":"4x3min"},
            {"icon":"💪","name":"Push-up Hold at Bottom","detail":"Lower to bottom of push-up, hold 3 seconds, push up. Repeat.","benefit":"Isometric strength for stabilising positions under pressure.","tags":["Chest","No Equipment"],"sets":"4x10"},
            {"icon":"🦵","name":"Balance Stand","detail":"Stand on one leg with eyes closed. Switch every 30 seconds.","benefit":"Proprioception and balance — prevents injuries in dynamic sport.","tags":["Balance","No Equipment"],"sets":"4x30sec each"},
            {"icon":"🏃","name":"Footwork Drill","detail":"Mark 4 spots on ground, move between them in pattern. Fast feet.","benefit":"Foot speed and directional change specific to your sport.","tags":["Footwork","No Equipment"],"sets":"4x90sec"},
            {"icon":"💪","name":"Slow Eccentric Push-ups","detail":"Lower for 5 seconds, hold 2 seconds at bottom, push up normal.","benefit":"Eccentric strength prevents muscle injuries during sport.","tags":["Chest","No Equipment"],"sets":"4x8"},
            {"icon":"🦵","name":"Lateral Step Pattern","detail":"Step left-together-left, right-together-right. Increase speed.","benefit":"Lateral movement patterns specific to court and field sports.","tags":["Agility","No Equipment"],"sets":"4x60sec"},
            {"icon":"🏃","name":"Reaction Drill","detail":"Stand ready, drop to ground on signal (clap), jump up fast.","benefit":"Reaction time and explosive recovery — game-changing skill.","tags":["Reaction","No Equipment"],"sets":"5x10"},
            {"icon":"💪","name":"Wrist Strengthening","detail":"Hold water bottle, flex and extend wrist slowly. Full range.","benefit":"Wrist strength prevents injury and improves grip in all sports.","tags":["Wrist","Water Bottle"],"sets":"3x15 each"},
            {"icon":"🦵","name":"Hip Flexor Stretch Hold","detail":"Lunge forward, drop back knee, push hips forward. Hold.","benefit":"Hip flexor flexibility for powerful leg drive and injury prevention.","tags":["Flexibility","No Equipment"],"sets":"3x45sec each"},
            {"icon":"🏃","name":"Cool-down Jog","detail":"Light jog at 50% effort. Focus on breathing and form.","benefit":"Active recovery reduces soreness and prepares body for next session.","tags":["Recovery","No Equipment"],"sets":"1x10min"},
        ],
        'sat': [
            {"icon":"🏅","name":"Full Sport Simulation","detail":"Simulate a full game/match/race scenario for 10 minutes. Full effort.","benefit":"Combines all training — the closest thing to real competition.","tags":["Match Sim","No Equipment"],"sets":"2x10min"},
            {"icon":"💪","name":"Circuit Training","detail":"Push-ups 15, squats 20, burpees 10. Rest 60 sec. Repeat.","benefit":"Sport conditioning — builds ability to perform when tired.","tags":["Conditioning","No Equipment"],"sets":"4 rounds"},
            {"icon":"🦵","name":"Sprint Intervals","detail":"Sprint 30m, walk 30m. Full effort on every sprint.","benefit":"Speed endurance — maintains sprint speed late in competition.","tags":["Speed","No Equipment"],"sets":"8x30m"},
            {"icon":"🏃","name":"Agility Pattern","detail":"Set 6 stones in pattern, move through touching each one.","benefit":"Change of direction and agility specific to your sport.","tags":["Agility","Stones"],"sets":"4x2min"},
            {"icon":"💪","name":"Strength Finisher","detail":"Max push-ups, then max squats, then max lunges. No rest between.","benefit":"Muscular endurance when glycogen is depleted — end-of-game strength.","tags":["Strength","No Equipment"],"sets":"3 rounds"},
            {"icon":"🦵","name":"Plyometric Sequence","detail":"5 jump squats, 5 broad jumps, 5 lateral bounds. No rest.","benefit":"Explosive power sequence — builds fast-twitch muscle fibers.","tags":["Power","No Equipment"],"sets":"4 rounds"},
            {"icon":"🏃","name":"Skill Repetition","detail":"Repeat the single most important skill of your sport 50 times.","benefit":"Volume repetition builds automatic muscle memory for key skills.","tags":["Skill","No Equipment"],"sets":"50 reps"},
            {"icon":"💪","name":"Core Superset","detail":"Plank 30sec, sit-ups 15, flutter kicks 30sec. No rest.","benefit":"Core endurance for maintaining technique when fatigued.","tags":["Core","No Equipment"],"sets":"4 rounds"},
            {"icon":"🦵","name":"Balance Challenge","detail":"Single leg squat holding position 5 sec at bottom. Slow and controlled.","benefit":"Balance and proprioception for injury-free athletic performance.","tags":["Balance","No Equipment"],"sets":"3x8 each"},
            {"icon":"🏃","name":"Breathing Drill","detail":"Jog slowly, inhale 4 steps, exhale 4 steps. Focus only on breath.","benefit":"Breathing control under exertion — recover faster between efforts.","tags":["Recovery","No Equipment"],"sets":"1x8min"},
        ],
    }

    sport_name = SPORTS_EN.get(sport, sport.title())
    phases = ["Foundation","Development","Intensity","Peak"]
    descriptions = [
        f"Build base fitness and learn {sport_name} movement patterns.",
        f"Increase volume and develop sport-specific skills.",
        "Push harder — more sets, less rest. Performance focus.",
        "Peak week — maximum intensity, competition-ready.",
    ]
    tips = [
        "Focus on perfect form — speed comes later.",
        "Push past your comfort zone — that's where improvement happens.",
        "Minimal rest between sets — build mental toughness.",
        "Give 100% on every rep — competition intensity starts now.",
    ]

    # Use sport-specific days if available, else generic
    day_pool = ALL_DAY_EXERCISES.get(sport, GENERIC_DAYS)

    day_keys   = ['mon','tue','wed','thu','fri','sat','sun']
    day_titles = ["Strength & Power","Speed & Agility","REST DAY","Endurance","Technique",f"{sport_name} Drills","REST DAY"]
    day_focus  = [f"{sport_name} strength",f"{sport_name} speed","Recovery","Stamina",f"{sport_name} technique","Sport drills","Rest"]

    weeks = []
    for w in range(4):
        days = []
        for i, day in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
            is_rest = (i == 2 or i == 6)
            scaled = []
            if not is_rest:
                key = day_keys[i]
                source = day_pool.get(key, GENERIC_DAYS.get(key, []))
                for ex in source:
                    e = dict(ex)
                    parts = e["sets"].split("x")
                    if len(parts) == 2:
                        try: e["sets"] = f"{int(parts[0])+w}x{parts[1]}"
                        except: pass
                    scaled.append(e)
            days.append({
                "day": day,
                "title": day_titles[i],
                "rest": is_rest,
                "focus": day_focus[i],
                "duration_min": (45 + w*5) if not is_rest else 0,
                "warmup": "5 min light jog + arm circles + hip rotations + leg swings",
                "cooldown": "5 min static stretch — quads, hamstrings, hip flexors, shoulders",
                "coach_tip": tips[w],
                "exercises": scaled,
            })
        weeks.append({"week":w+1,"phase":phases[w],"description":descriptions[w],"days":days})
    return json.dumps({"sport":sport_name,"level":level,"weeks":weeks})


class AIService:
    def __init__(self):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            print("⚠  WARNING: No GEMINI_API_KEY found in .env — AI plans will not work.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=api_key)
                print("✅ Gemini AI connected successfully.")
            except Exception as e:
                print(f"⚠  Could not connect to Gemini: {e}")
                self.client = None

    def _sport_name(self, sport, language='en'):
        if language == 'hi':
            return SPORTS_HINDI.get(sport, sport)
        return SPORTS_EN.get(sport, sport.replace('_', '-').title())

    def _call_ai(self, prompt):
        response = self.client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text

    def _parse_json(self, text):
        clean = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
        return json.loads(clean)

    def _no_client_error(self):
        raise Exception("GEMINI_API_KEY not found. Please add it to your .env file and restart the server.")

    # ── Workout Plan ──────────────────────────────────────────────────────────

    def generate_workout_plan(self, user):
        if not self.client:
            self._no_client_error()

        sport      = user.get('sport', 'athletics')
        level      = user.get('fitness_level', 'beginner')
        age        = user.get('age', 20)
        weight     = user.get('weight', '') or 'unknown'
        gender     = user.get('gender', 'male')
        sport_name = self._sport_name(sport, 'en')
        level_desc = LEVEL_DESCRIPTION.get(level, level)
        sport_icon = SPORT_ICONS.get(sport, '🏅')

        # Gender-specific coaching notes
        if gender == 'female':
            gender_note = "Athlete is FEMALE. Focus more on core stability, hip strength, flexibility. Adjust intensity for female physiology."
        elif gender == 'male':
            gender_note = "Athlete is MALE. Focus on explosive power, upper body strength, and speed."
        else:
            gender_note = "Focus on balanced full-body fitness."

        print(f"🎯 Generating workout plan for: {sport_name} | {level} | {gender} | age {age}")

        prompt = f"""You are AthleteAI, a personal sports coach for Indian athletes.

ATHLETE PROFILE:
- Sport: {sport_name}
- Gender: {gender} — {gender_note}
- Age: {age}, Weight: {weight}kg
- Fitness level: {level_desc}

Generate a 4-week workout plan specifically for {sport_name}. Return ONLY valid JSON, no extra text, no markdown fences.

JSON structure:
{{
  "sport": "{sport_name}",
  "level": "{level}",
  "weeks": [
    {{
      "week": 1,
      "phase": "Foundation",
      "description": "Short week goal description",
      "days": [
        {{
          "day": "Mon",
          "title": "Lower Body Power",
          "rest": false,
          "focus": "Quads · Hamstrings",
          "duration_min": 60,
          "warmup": "Warmup description",
          "cooldown": "Cooldown description",
          "coach_tip": "One tip specific to {sport_name}",
          "exercises": [
            {{
              "icon": "🦵",
              "name": "Exercise name",
              "detail": "Step-by-step: how to do this exercise using household items",
              "benefit": "Why this exercise directly helps your {sport_name} performance",
              "tags": ["Muscle group", "Equipment type"],
              "sets": "4x15"
            }}
          ]
        }}
      ]
    }}
  ]
}}

STRICT RULES:
- All 7 days: Mon, Tue, Wed, Thu, Fri, Sat, Sun
- Wed and Sun: rest:true, exercises:[]
- Sat: {sport_name}-specific technique drills only, use icon {sport_icon}
- ZERO gym equipment — only water bottles, bricks, chairs, walls, stairs, rope, open ground
- Every exercise must directly build skills for {sport_name} — no generic plans
- EVERY DAY must have DIFFERENT exercises — never repeat the same exercise on two different days
- Each day has a different focus: Mon=Strength, Tue=Speed/Agility, Thu=Endurance, Fri=Technique, Sat=Sport Drills
- coach_tip must be specific to {sport_name} technique or strategy
- Each week progressively harder (increase sets/reps/intensity each week)
- EXACTLY 10 exercises per training day — no more, no less
- benefit field: 1 sentence explaining exactly how this exercise improves {sport_name} performance
- Return ONLY the JSON object, nothing else"""

        try:
            raw = self._call_ai(prompt)
            parsed = self._parse_json(raw)
            assert 'weeks' in parsed and len(parsed['weeks']) > 0
            print(f"✅ Workout plan generated successfully for {sport_name}")
            return json.dumps(parsed)
        except Exception as e:
            print(f"⚠  AI failed for workout, using built-in plan: {e}")
            return _build_fallback_workout(sport, level)

    # ── Nutrition Plan ────────────────────────────────────────────────────────

    def generate_nutrition_plan(self, user):
        if not self.client:
            self._no_client_error()

        sport      = user.get('sport', 'athletics')
        level      = user.get('fitness_level', 'beginner')
        age        = user.get('age', 20)
        weight     = user.get('weight', '65') or '65'
        sport_name = self._sport_name(sport, 'en')

        strength_sports  = ['wrestling', 'boxing', 'judo', 'weightlifting']
        endurance_sports = ['athletics', 'swimming', 'football', 'hockey', 'kabaddi', 'kho_kho']
        if sport in strength_sports:
            macro_focus = 'High protein (1.6-2g per kg bodyweight). More eggs, dal, peanuts, milk.'
        elif sport in endurance_sports:
            macro_focus = 'High carbs for energy. More rice, banana, roti, sattu. Moderate protein.'
        else:
            macro_focus = 'Balanced carbs and protein. Mix of roti, dal, eggs, banana.'

        print(f"🥗 Generating nutrition plan for: {sport_name} | {weight}kg")

        prompt = f"""You are AthleteAI, a sports nutritionist for Indian athletes from low-income backgrounds.

ATHLETE: {sport_name} athlete, age {age}, weight {weight}kg, level {level}
NUTRITION FOCUS: {macro_focus}

Generate a daily nutrition plan. Return ONLY valid JSON, no extra text, no markdown fences.

JSON structure:
{{
  "daily_cost_range": "Rs.80-120",
  "tags": ["100% Indian foods", "High protein"],
  "meals": [
    {{
      "time": "5:30 AM",
      "type": "Wake-up drink",
      "name": "Meal name",
      "cost": "Rs.2",
      "items": ["Warm water", "Lemon", "Pinch of salt"],
      "highlight": ["Lemon"]
    }}
  ],
  "avoid": ["Cold drinks", "Maida"],
  "hydration": "3-4 litres per day",
  "natural_supplements": ["Peanuts for protein", "Banana before training"]
}}

RULES:
- Under Rs.100-150 per day total
- Only Indian foods: roti, rice, dal, chana, rajma, eggs, milk, curd, peanuts, banana, sattu, seasonal sabzi
- 6-7 meals/snacks timed around a 4:30 PM training session
- highlight array = the most important protein/energy items in that meal
- Nutrition must be tailored specifically for {sport_name} demands
- Return ONLY the JSON object, nothing else"""

        try:
            parsed = self._parse_json(self._call_ai(prompt))
            assert 'meals' in parsed
            print(f"✅ Nutrition plan generated successfully for {sport_name}")
            return json.dumps(parsed)
        except Exception as e:
            print(f"⚠  AI failed for nutrition, using built-in plan: {e}")
            return json.dumps(FALLBACK_NUTRITION.get(sport, DEFAULT_NUTRITION))

    # ── Photo Analysis ────────────────────────────────────────────────────────

    def analyze_photo(self, photo_bytes, content_type, user=None):
        if not self.client:
            self._no_client_error()

        language   = user.get('language', 'en') if user else 'en'
        sport      = user.get('sport', 'athletics') if user else 'athletics'
        sport_name = self._sport_name(sport, language)
        lang_instr = "Respond ENTIRELY in Hindi (Devanagari script)." if language == 'hi' \
                     else "Respond in clear, simple English."

        try:
            import PIL.Image, io, base64
            img      = PIL.Image.open(io.BytesIO(photo_bytes))
            buf      = io.BytesIO()
            img.save(buf, format='JPEG')
            b64      = base64.b64encode(buf.getvalue()).decode()

            from google.genai import types
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[
                    types.Part.from_bytes(data=base64.b64decode(b64), mime_type='image/jpeg'),
                    f"""You are AthleteAI analysing a photo for a {sport_name} athlete from India.
Provide: body composition, posture issues for {sport_name}, key strengths, top 3 improvements,
3-5 household-item exercises specific to {sport_name}, and a motivational message.
Be encouraging and culturally sensitive. {lang_instr}"""
                ]
            )
            return response.text
        except Exception as e:
            print(f"[photo] Error: {e}")
            raise Exception("Could not analyse photo. Please try again.")
