import discord
import asyncio
import requests
import sqlite3
import os
from discord.ext import commands

# Bot Token
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "snipes.db")
RUTGERS_API_URL = "https://sis.rutgers.edu/soc/api/courses.json?year=2025&term=1&campus=NB"
SCAN_INTERVAL = 2  # Check every 2 seconds

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize SQLite database
async def initialize_storage():
    os.makedirs("data", exist_ok=True)  # Ensure data folder exists
    with sqlite3.connect(SQL_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS snipes (
                discord_id TEXT,
                index_number TEXT,
                notifications_sent INTEGER DEFAULT 0,
                UNIQUE(discord_id, index_number)  -- Prevent duplicate snipes
            )
        """)
        conn.commit()

# Add a course snipe for a user (Prevents Duplicates)
async def add_snipe(discord_id, index_number):
    with sqlite3.connect(SQL_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM snipes WHERE discord_id = ?", (discord_id,))
        if c.fetchone()[0] >= 10:
            return False  # Max 10 snipes per user
        try:
            c.execute("""
                INSERT INTO snipes (discord_id, index_number, notifications_sent)
                VALUES (?, ?, 0)
            """, (discord_id, index_number))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return "duplicate"  # Duplicate snipe detected

# Fetch all courses from the Rutgers API
async def fetch_courses():
    try:
        response = requests.get(RUTGERS_API_URL)
        if response.status_code == 200:
            return response.json()
        print("❌ API returned non-200 status:", response.status_code)
    except Exception as e:
        print("🔥 API request failed:", e)
    return []

# A helper to fetch the course name by index_number
def get_course_name(index_number):
    try:
        response = requests.get(RUTGERS_API_URL)
        if response.status_code == 200:
            courses = response.json()
            for course in courses:
                course_title = course.get("title", "Unknown Course")
                subject = course.get("subject", "Unknown Subject")
                course_number = course.get("courseNumber", "XXX")
                for section in course.get("sections", []):
                    if str(section.get("index")) == str(index_number):
                        return f"{subject} {course_number} - {course_title}"
    except Exception as e:
        print(f"❌ Error fetching course name for index {index_number}: {e}")
    return f"Unknown Course ({index_number})"

# Notify users when a course opens (Spam up to 5 times, then auto-delete)
async def notify_users(index_number):
    print(f"🔍 Notifying users for course {index_number}...")
    with sqlite3.connect(SQL_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT discord_id, notifications_sent
            FROM snipes
            WHERE index_number = ?
        """, (index_number,))
        users = c.fetchall()

        for user_id, sent_count in users:
            if sent_count < 5:  # Only send if user has received less than 5 messages
                try:
                    user = await bot.fetch_user(int(user_id))
                    if user:
                        course_name = get_course_name(index_number)
                        await user.send(
                            f"🔔 <@{user_id}>, the course **{course_name}** (index {index_number}) is now OPEN! (Notification {sent_count + 1}/5)"
                        )
                        print(f"✅ Sent DM to user {user_id} (#{sent_count+1})")
                except discord.HTTPException as e:
                    print(f"❌ Failed to send message to {user_id}: {e}")

                # Update notifications_sent count
                c.execute("""
                    UPDATE snipes
                    SET notifications_sent = notifications_sent + 1
                    WHERE discord_id = ? AND index_number = ?
                """, (user_id, index_number))

                # If user has received all 5 notifications, delete the snipe
                if sent_count + 1 >= 5:
                    c.execute("""
                        DELETE FROM snipes
                        WHERE discord_id = ? AND index_number = ?
                    """, (user_id, index_number))
                    print(f"🗑 Deleted snipe for {user_id} - {index_number} after 5 notifications.")

        conn.commit()

# Check courses every 2 seconds
async def check_courses():
    while True:
        try:
            print("🔄 Checking courses...")
            with sqlite3.connect(SQL_FILE) as conn:
                c = conn.cursor()
                c.execute("SELECT DISTINCT index_number FROM snipes")
                tracked_courses = {row[0] for row in c.fetchall()}

            courses = await fetch_courses()
            for course in courses:
                for section in course.get("sections", []):
                    index_number = section.get("index")
                    status = str(section.get("openStatus")).strip().upper()

                    print(f"🔎 Course {index_number}: {status}")

                    # Notify users if course is open
                    if str(index_number) in tracked_courses and status == "TRUE":
                        print(f"✅ Course {index_number} is OPEN! Notifying users...")
                        await notify_users(index_number)

            await asyncio.sleep(SCAN_INTERVAL)  # Check every 2 seconds
        except Exception as e:
            print(f"🔥 check_courses() crashed: {e}")

# Command: !snipe <index_number>
@bot.command()
async def snipe(ctx, index_number: str):
    result = await add_snipe(str(ctx.author.id), index_number)
    course_name = get_course_name(index_number)

    if result == True:
        await ctx.send(f"✅ <@{ctx.author.id}>, you will be notified when the course **{course_name}** (index {index_number}) opens!")
    elif result == "duplicate":
        await ctx.send(f"⚠️ <@{ctx.author.id}>, you are already sniping the course **{course_name}** (index {index_number})!")
    else:
        await ctx.send("❌ You have reached the limit of 10 snipes.")

# Command: !my_snipes (Show user's active snipes)
@bot.command()
async def my_snipes(ctx):
    with sqlite3.connect(SQL_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT index_number FROM snipes WHERE discord_id = ?", (str(ctx.author.id),))
        snipes = [row[0] for row in c.fetchall()]

    if snipes:
        # Build a list with index plus the course name
        snipes_list = []
        for index_num in snipes:
            course_name = get_course_name(index_num)
            snipes_list.append(f"({course_name})")

        snipes_str = ", \n".join(snipes_list)
        await ctx.send(f"📋 <@{ctx.author.id}>\nYour active snipes:\n{snipes_str}")
    else:
        await ctx.send(f"ℹ️ <@{ctx.author.id}>, you have no active snipes.")

# Command: !clear_snipes (Remove all snipes for user)
@bot.command()
async def clear_snipes(ctx):
    with sqlite3.connect(SQL_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM snipes WHERE discord_id = ?", (str(ctx.author.id),))
        conn.commit()

    await ctx.send(f"🗑 <@{ctx.author.id}>, all your snipes have been removed!")

# Command: !remove_snipe <index> (Remove a single snipe by index)
@bot.command()
async def remove_snipe(ctx, index_number: str):
    with sqlite3.connect(SQL_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM snipes WHERE discord_id = ? AND index_number = ?", (str(ctx.author.id), index_number))
        conn.commit()

    await ctx.send(f"✅ <@{ctx.author.id}>, removed snipe for index **{index_number}**!")


# Command: !commands (List available commands)
@bot.command(name="commands" or "help")
async def commands(ctx):
    help_message = """📖 **Sniper Bot Commands:**
```txt
!snipe <index_number>` → Add a course to your snipes.
!my_snipes` → List your active snipes with course names.
!remove_snipe <index_number>` → Remove a specific snipe.
!clear_snipes` → Remove all your snipes.

The bot will spam you 5 times when a sniped course opens! 🚀
    ```
    """
    
    await ctx.send(help_message)


# Bot ready event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await initialize_storage()
    asyncio.create_task(check_courses())  
    print("🚀 Started monitoring courses!")

# Run the bot
bot.run(TOKEN)
