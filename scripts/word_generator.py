import random
import urllib.request
import json
import re

# Comprehensive offline bank of clean, common, easy 3-6 letter English words
BASE_EASY_WORDS = [
    # 3 letters
    "AIR", "ALL", "AND", "ANY", "ARM", "ART", "ASK", "BAD", "BAG", "BAR",
    "BAT", "BED", "BEE", "BIG", "BOX", "BOY", "BUS", "BUY", "CAN", "CAR",
    "CAT", "COW", "CRY", "CUP", "CUT", "DAY", "DOG", "DRY", "EAR", "EAT",
    "EGG", "END", "EYE", "FAN", "FAR", "FAT", "FEW", "FIT", "FLY", "FOR",
    "FOX", "FUN", "GAS", "GET", "GOD", "GUN", "GUY", "HAT", "HIT", "HOT",
    "ICE", "INK", "JAR", "JAW", "JOY", "KEY", "KID", "LAP", "LAW", "LEG",
    "LET", "LIP", "LOW", "MAN", "MAP", "MAY", "MIX", "MOM", "MUD", "NET",
    "NEW", "NOD", "NOT", "NOW", "NUT", "OAK", "ODD", "OFF", "OIL", "OLD",
    "ONE", "OUR", "OUT", "OWL", "PAN", "PAY", "PEN", "PET", "PIE", "PIG",
    "PIN", "POT", "RAY", "RED", "RIB", "ROD", "ROW", "RUB", "RUG", "RUN",
    "SAD", "SAW", "SAY", "SEA", "SEE", "SET", "SEW", "SHY", "SIN", "SIR",
    "SIT", "SIX", "SKI", "SKY", "SON", "SPY", "SUN", "TAG", "TEA", "TEN",
    "THE", "TIE", "TIP", "TOE", "TOP", "TOY", "TRY", "TWO", "USE", "VAN",
    "WAR", "WAY", "WET", "WHO", "WHY", "WIN", "YES", "YET", "ZOO",

    # 4 letters
    "ABLE", "ACID", "AGED", "ALSO", "AREA", "ARMY", "AWAY", "BABY", "BACK",
    "BALL", "BAND", "BANK", "BASE", "BATH", "BEAR", "BEAT", "BEEN", "BELL",
    "BEST", "BIRD", "BLOW", "BLUE", "BOAT", "BODY", "BONE", "BOOK", "BORN",
    "BOTH", "BOWL", "BUSY", "CALL", "CALM", "CAME", "CAMP", "CARD", "CARE",
    "CASE", "CITY", "COLD", "COME", "COOK", "COOL", "COPY", "DARK", "DATE",
    "DAWN", "DEAL", "DEAR", "DEEP", "DESK", "DIET", "DOOR", "DOWN", "DRAW",
    "DROP", "DUCK", "DUST", "DUTY", "EACH", "EARN", "EAST", "EASY", "EDGE",
    "EVEN", "EVER", "FACE", "FACT", "FAIL", "FAIR", "FALL", "FARM", "FAST",
    "FEAR", "FEED", "FEEL", "FILL", "FILM", "FIND", "FINE", "FIRE", "FISH",
    "FIVE", "FLAT", "FLOW", "FOOD", "FOOT", "FREE", "FROG", "FULL", "GAME",
    "GATE", "GIFT", "GIRL", "GIVE", "GLAD", "GOAL", "GOLD", "GOOD", "GRAY",
    "GROW", "HAIR", "HALF", "HAND", "HARD", "HAVE", "HEAD", "HEAR", "HELP",
    "HERO", "HIGH", "HILL", "HOLD", "HOLE", "HOME", "HOPE", "HOUR", "HUGE",
    "ICON", "IDEA", "IRON", "ITEM", "JOIN", "JUMP", "JUST", "KEEP", "KICK",
    "KIND", "KING", "KISS", "KNEE", "KNOW", "LAKE", "LAMP", "LAND", "LANE",
    "LAST", "LATE", "LEAD", "LEAF", "LEFT", "LIFE", "LIFT", "LIKE", "LINE",
    "LION", "LIST", "LIVE", "LOAD", "LOCK", "LONG", "LOOK", "LOVE", "LUCK",
    "MADE", "MAKE", "MANY", "MARK", "MATH", "MEAL", "MEET", "MILD", "MILK",
    "MIND", "MINE", "MOON", "MORE", "MOST", "MOVE", "MUCH", "NAME", "NEAR",
    "NECK", "NEED", "NEWS", "NEXT", "NICE", "NINE", "NOSE", "NOTE", "OPEN",
    "OVER", "PAGE", "PAIN", "PARK", "PART", "PASS", "PAST", "PATH", "PEAK",
    "PLAN", "PLAY", "POEM", "POET", "POND", "POOR", "POST", "PURE", "RAIN",
    "READ", "REAL", "REST", "RICH", "RIDE", "RING", "RISE", "ROAD", "ROCK",
    "ROOF", "ROOM", "ROOT", "ROSE", "SAFE", "SAID", "SAIL", "SALT", "SAME",
    "SAND", "SAVE", "SEAT", "SEED", "SEEK", "SEEM", "SEEN", "SEND", "SHIP",
    "SHOE", "SHOP", "SHOT", "SHOW", "SIDE", "SIGN", "SILK", "SING", "SINK",
    "SITE", "SIZE", "SKIN", "SLOW", "SNOW", "SOFT", "SOIL", "SONG", "SOON",
    "SOUL", "STAR", "STAY", "STEP", "STOP", "SUCH", "SURE", "TAKE", "TALK",
    "TALL", "TEAM", "TELL", "TERM", "TEST", "TEXT", "THAT", "THEM", "THEN",
    "THEY", "THIN", "THIS", "TIME", "TINY", "TOLD", "TOOK", "TOOL", "TOWN",
    "TREE", "TRUE", "TUNE", "TURN", "UNIT", "UPON", "VAST", "VERY", "VIEW",
    "VOTE", "WALK", "WALL", "WANT", "WARM", "WASH", "WAVE", "WEEK", "WELL",
    "WENT", "WEST", "WHAT", "WHEN", "WIDE", "WIFE", "WILD", "WILL", "WIND",
    "WING", "WISE", "WISH", "WITH", "WOOD", "WORD", "WORK", "YARD", "YEAR",

    # 5 letters
    "ABOUT", "ABOVE", "ACTOR", "ADMIT", "ADOPT", "AFTER", "AGAIN", "AGENT",
    "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIKE", "ALIVE", "ALLOW",
    "ALONE", "ALONG", "ALTER", "AMONG", "ANGEL", "ANGER", "ANGLE", "ANGRY",
    "APART", "APPLE", "APPLY", "ARENA", "ARGUE", "ARISE", "ARMED", "ARRAY",
    "ARROW", "ASIDE", "ASSET", "AVOID", "AWAKE", "AWARD", "AWARE", "BADLY",
    "BAKER", "BASIC", "BEACH", "BEGAN", "BEGIN", "BEING", "BELOW", "BENCH",
    "BIRTH", "BLACK", "BLAME", "BLANK", "BLIND", "BLOCK", "BLOOD", "BOARD",
    "BOOST", "BOOTH", "BRAIN", "BRAVE", "BREAD", "BREAK", "BRICK", "BRIEF",
    "BRING", "BROAD", "BROWN", "BRUSH", "BUILD", "BUILT", "CABIN", "CABLE",
    "CAMEL", "CANAL", "CANDY", "CATCH", "CAUSE", "CHAIN", "CHAIR", "CHALK",
    "CHAMP", "CHART", "CHASE", "CHEAP", "CHECK", "CHEST", "CHIEF", "CHILD",
    "CIVIL", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLIMB", "CLOCK", "CLOSE",
    "CLOUD", "COACH", "COAST", "COLOR", "CRAFT", "CRANE", "CRASH", "CREAM",
    "CRIME", "CROSS", "CROWD", "CROWN", "DAILY", "DANCE", "DREAM", "DRIVE",
    "EARLY", "EARTH", "EIGHT", "ELITE", "EMPTY", "ENEMY", "ENJOY", "ENTER",
    "ENTRY", "EQUAL", "ERROR", "EVENT", "EVERY", "EXACT", "EXIST", "EXTRA",
    "FAITH", "FALSE", "FANCY", "FAULT", "FIBER", "FIELD", "FIFTH", "FIFTY",
    "FIGHT", "FINAL", "FIRST", "FLAME", "FLASH", "FLEET", "FLOAT", "FLOOD",
    "FLOOR", "FLOUR", "FLUID", "FOCUS", "FORCE", "FORTH", "FORTY", "FORUM",
    "FOUND", "FRAME", "FRESH", "FRONT", "FRUIT", "GIANT", "GIVEN", "GLASS",
    "GLOBE", "GLORY", "GRACE", "GRADE", "GRAIN", "GRAND", "GRANT", "GRASS",
    "GRAVE", "GREAT", "GREEN", "GREET", "GUEST", "GUIDE", "HABIT", "HAPPY",
    "HEART", "HEAVY", "HONOR", "HORSE", "HOTEL", "HOUSE", "HUMAN", "IDEAL",
    "IMAGE", "INDEX", "INNER", "INPUT", "ISSUE", "JELLY", "JEWEL", "JUICE",
    "KNIFE", "KNOCK", "LABEL", "LABOR", "LARGE", "LASER", "LATER", "LAUGH",
    "LAYER", "LEARN", "LEAST", "LEAVE", "LEGAL", "LEMON", "LEVEL", "LIGHT",
    "LIMIT", "LOCAL", "LOGIC", "LUCKY", "LUNCH", "MAGIC", "MAJOR", "MAKER",
    "MARCH", "MATCH", "MAYOR", "MEDIA", "METAL", "METER", "MIGHT", "MODEL",
    "MONEY", "MONTH", "MORAL", "MOTOR", "MOUNT", "MOUSE", "MOUTH", "MOVIE",
    "MUSIC", "NAKED", "NERVE", "NIGHT", "NOBLE", "NOISE", "NORTH", "NOVEL",
    "NURSE", "OCEAN", "OFFER", "OFTEN", "ONION", "ORDER", "ORGAN", "OTHER",
    "PAINT", "PANEL", "PAPER", "PARTY", "PEACE", "PHASE", "PHONE", "PHOTO",
    "PIANO", "PIECE", "PILOT", "PITCH", "PLACE", "PLAIN", "PLANE", "PLANT",
    "PLATE", "POINT", "POUND", "POWER", "PRESS", "PRICE", "PRIDE", "PRIME",
    "PRINT", "PRIZE", "PROOF", "PROUD", "PUPIL", "QUEEN", "QUICK", "QUIET",
    "RADIO", "RAISE", "RANGE", "RAPID", "RATIO", "REACH", "REACT", "READY",
    "RIVER", "ROBOT", "ROUND", "ROUTE", "ROYAL", "RULER", "RURAL", "SCALE",
    "SCENE", "SCOPE", "SCORE", "SENSE", "SERVE", "SHAKE", "SHARE", "SHARP",
    "SHEEP", "SHEET", "SHELF", "SHELL", "SHIFT", "SHINE", "SHIRT", "SHOCK",
    "SHOOT", "SIGHT", "SILK", "SILLY", "SINCE", "SKILL", "SLATE", "SLEEP",
    "SLIDE", "SMART", "SMILE", "SMOKE", "SOLAR", "SOLID", "SOLVE", "SOUND",
    "SOUTH", "SPACE", "SPARE", "SPEAK", "SPEED", "SPEND", "SPICE", "SPORT",
    "STAGE", "STAND", "START", "STATE", "STEAM", "STEEL", "STICK", "STILL",
    "STOCK", "STONE", "STORE", "STORM", "STORY", "STRIP", "SUGAR", "SUITE",
    "SUPER", "SWEET", "SWIFT", "SWING", "TABLE", "TASTE", "TEACH", "THANK",
    "THEME", "THICK", "THING", "THINK", "THIRD", "TIGER", "TITLE", "TODAY",
    "TOOTH", "TOPIC", "TOTAL", "TOUCH", "TOWER", "TRACK", "TRADE", "TRAIN",
    "TREAT", "TREND", "TRIAL", "TRIBE", "TRICK", "TRUCK", "TRULY", "TRUST",
    "TRUTH", "TWICE", "UNDER", "UNION", "UNITY", "UPPER", "UPSET", "URBAN",
    "USAGE", "USUAL", "VALID", "VALUE", "VAPOR", "VIDEO", "VIRUS", "VISIT",
    "VITAL", "VOICE", "WASTE", "WATCH", "WATER", "WHEEL", "WHERE", "WHICH",
    "WHILE", "WHITE", "WHOLE", "WOMAN", "WORLD", "WORRY", "WORTH", "YOUTH",

    # 6 letters
    "ACTION", "ACTIVE", "ACTUAL", "ADVICE", "AFFORD", "ALWAYS", "ANIMAL",
    "ANSWER", "APPEAL", "APPEAR", "AROUND", "ARRIVE", "ARTIST", "ASPECT",
    "AUTUMN", "AVENUE", "BEAUTY", "BECOME", "BEFORE", "BEHIND", "BELIEF",
    "BELONG", "BETTER", "BEYOND", "BITTER", "BLOUSE", "BORDER", "BORROW",
    "BOTTLE", "BOUNCE", "BRANCH", "BREEZE", "BRIDGE", "BRIGHT", "BROKEN",
    "BUDGET", "BURDEN", "BUTTER", "BUTTON", "CAMERA", "CANDLE", "CANYON",
    "CARPET", "CASTLE", "CASUAL", "CENTER", "CHANCE", "CHANGE", "CHARGE",
    "CHEESE", "CHERRY", "CHURCH", "CIRCLE", "CLEVER", "CLIMATE", "CLOUDY",
    "COFFEE", "COLDLY", "COLOUR", "COMMON", "COOKIE", "CORNER", "COSTLY",
    "COTTON", "COUNTY", "COUPLE", "COURSE", "COUSIN", "CREDIT", "CUSTOM",
    "DAMAGE", "DANCER", "DANGER", "DECENT", "DECIDE", "DEFEAT", "DEGREE",
    "DEMAND", "DESIGN", "DESIRE", "DETAIL", "DEVICE", "DINNER", "DIRECT",
    "DOCTOR", "DOLLAR", "DOMAIN", "DOUBLE", "DRAGON", "DREAMS", "DRIVEN",
    "DRIVER", "EARTHY", "EASILY", "EFFORT", "ELEVEN", "ENERGY", "ENGINE",
    "ENOUGH", "ENTIRE", "ESCAPE", "ESTATE", "EVENING", "EXCEPT", "EXCUSE",
    "EXPECT", "EXPERT", "EXPORT", "EXTENT", "FACTOR", "FAMILY", "FAMOUS",
    "FARMER", "FATHER", "FELLOW", "FEMALE", "FINGER", "FINISH", "FLIGHT",
    "FLOWER", "FLYING", "FOLLOW", "FOREST", "FORGET", "FORMAL", "FOSTER",
    "FOURTH", "FREEZE", "FRIEND", "FUTURE", "GALAXY", "GARDEN", "GATHER",
    "GENTLE", "GIFTED", "GLANCE", "GLOBAL", "GOLDEN", "GOSPEL", "GRANNY",
    "GRAPES", "GROUND", "GROWTH", "GUITAR", "HAMMER", "HANDLE", "HAPPEN",
    "HARBOR", "HARDLY", "HEALTH", "HEAVEN", "HEIGHT", "HEROIC", "HIDDEN",
    "HONEST", "HONEYS", "HUNGER", "HUNTER", "IGNORE", "IMPACT", "IMPORT",
    "INCOME", "INFANT", "INFORM", "INSECT", "INSIDE", "INTACT", "INTEND",
    "INVEST", "INVITE", "ISLAND", "JACKET", "JOCKEY", "JOURNAL", "JUNGLE",
    "JUNIOR", "KERNEL", "KITTEN", "KNIGHT", "LADDER", "LANCER", "LAPTOP",
    "LATTER", "LEADER", "LEAGUE", "LEGEND", "LETTER", "LIGHTS", "LIKELY",
    "LIQUID", "LISTEN", "LITTLE", "LIVELY", "LIZARD", "LOCATE", "LONELY",
    "LOVELY", "LUMBER", "MAGNET", "MAIDEN", "MAINLY", "MANAGE", "MANNER",
    "MANUAL", "MARBLE", "MARGIN", "MARKET", "MASTER", "MATTER", "MEADOW",
    "MEDIUM", "MEMBER", "MEMORY", "MENTAL", "METHOD", "MIDDLE", "MILLER",
    "MINING", "MIRROR", "MOBILE", "MODERN", "MODEST", "MOMENT", "MONKEY",
    "MORTAL", "MOTHER", "MOTION", "MUSEUM", "MUTUAL", "MYSELF", "NATION",
    "NATIVE", "NATURE", "NEEDLE", "NOBODY", "NORMAL", "NOTICE", "NUMBER",
    "OBJECT", "OBTAIN", "OFFICE", "OFFSET", "ONLINE", "ORANGE", "ORIGIN",
    "OUTFIT", "OUTLET", "OUTPUT", "PALACE", "PANTRY", "PARADE", "PARCEL",
    "PARENT", "PARROT", "PASTOR", "PATENT", "PATHWAY", "PATROL", "PEANUT",
    "PENCIL", "PEOPLE", "PEPPER", "PERIOD", "PERSON", "PHRASE", "PICKLE",
    "PIGEON", "PILGRIM", "PILLAR", "PLANET", "PLENTY", "POCKET", "POETRY",
    "POLICE", "POLICY", "POLITE", "POSTER", "POTATO", "POWDER", "PRAISE",
    "PRAYER", "PRETTY", "PRINCE", "PRISON", "PROFIT", "PROMPT", "PROPER",
    "PUBLIC", "PULPIT", "PUNISH", "PUPPY", "PURPLE", "PURSUIT", "PUZZLE",
    "QUARRY", "RABBIT", "RADIAL", "REASON", "RECIPE", "RECORD", "REDUCE",
    "REFORM", "REFUGE", "REFUND", "REFUSE", "REGARD", "REGRET", "RELIEF",
    "REMAIN", "REMEDY", "REMIND", "REPAIR", "REPEAT", "REPORT", "RESCUE",
    "RESORT", "RESULT", "RETAIL", "RETAIN", "RETURN", "REVEAL", "REVIEW",
    "REWARD", "RHYTHM", "RIBBON", "RIDDLE", "RISING", "ROCKET", "ROLLER",
    "RUBBER", "RUNNER", "SADDLE", "SAFELY", "SAFETY", "SAILOR", "SAMPLE",
    "SAVING", "SCARCE", "SCHEME", "SCHOOL", "SCREAM", "SCREEN", "SCRIPT",
    "SEARCH", "SEASON", "SECOND", "SECRET", "SECTOR", "SECURE", "SELDOM",
    "SELECT", "SELLER", "SENIOR", "SERIES", "SETTLE", "SEVERE", "SHADOW",
    "SHIELD", "SHIVER", "SHRINE", "SIGNAL", "SILENT", "SILVER", "SIMPLE",
    "SINGER", "SINGLE", "SISTER", "SKETCH", "SLEEPY", "SLIGHT", "SLOWLY",
    "SMOOTH", "SOCCER", "SOCIAL", "SOCKET", "SODIUM", "SOLELY", "SORROW",
    "SOURCE", "SPEECH", "SPIRIT", "SPLASH", "SPREAD", "SPRING", "SQUARE",
    "STABLE", "STARVE", "STATUE", "STATUS", "STEADY", "STREAM", "STREET",
    "STRESS", "STRIKE", "STRING", "STROKE", "STRONG", "STUDIO", "SUBTLE",
    "SUDDEN", "SUFFER", "SUMMER", "SUMMIT", "SUNSET", "SUPPER", "SUPPLY",
    "SURELY", "SURVEY", "SWITCH", "SYMBOL", "SYSTEM", "TALENT", "TARGET",
    "TEMPLE", "TENDER", "TENNIS", "TERROR", "THEORY", "THIRST", "TIMBER",
    "TIMING", "TISSUE", "TOMATO", "TONGUE", "TOWARD", "TRAVEL", "TREATY",
    "TURKEY", "TWELVE", "TWENTY", "TYPICAL", "UNIQUE", "UPDATE", "URGENT",
    "VALLEY", "VALUED", "VECTOR", "VELVET", "VESSEL", "VICTIM", "VICTOR",
    "VIEWER", "VIOLET", "VIRTUE", "VISION", "VISUAL", "VOLUME", "VOYAGE",
    "WAFFLE", "WALNUT", "WARMTH", "WEALTH", "WEAPON", "WEEKLY", "WEIGHT",
    "WINDOW", "WINNER", "WINTER", "WISDOM", "WIZARD", "WONDER", "WOODEN",
    "WORKER", "WRITER", "YELLOW", "ZEPHYR"
]

# Ensure everything meets the 3-6 letter constraint and is clean A-Z
EASY_WORDS = [w for w in BASE_EASY_WORDS if 3 <= len(w) <= 6 and re.match(r"^[A-Z]+$", w)]

class WordGenerator:
    """Provides curated 3-6 letter easy English words for gameplay with zero startup latency."""

    _cached_api_words = []

    @classmethod
    def fetch_api_words(cls, count: int = 40, max_len: int = 6) -> list:
        """Fast offline return of cached words without blocking the game loop."""
        return cls._cached_api_words

    @classmethod
    def get_word_sequence(cls, total_notes: int) -> list:
        """Generates a non-repeating sequence of easy 3-6 letter words whose
        cumulative character count meets or exceeds total_notes.
        """
        combined_pool = list(set(EASY_WORDS + cls._cached_api_words))
        random.shuffle(combined_pool)

        sequence = []
        char_count = 0
        pool_index = 0

        while char_count < total_notes:
            remaining = total_notes - char_count
            if pool_index >= len(combined_pool):
                random.shuffle(combined_pool)
                if sequence and combined_pool[0] == sequence[-1] and len(combined_pool) > 1:
                    combined_pool[0], combined_pool[1] = combined_pool[1], combined_pool[0]
                pool_index = 0

            # If nearing the end and exact length match is available, pick it
            if 3 <= remaining <= 6:
                exact_matches = [w for w in combined_pool if len(w) == remaining and (not sequence or w != sequence[-1])]
                if exact_matches:
                    chosen_word = random.choice(exact_matches)
                    sequence.append(chosen_word)
                    char_count += len(chosen_word)
                    break

            chosen_word = combined_pool[pool_index]
            pool_index += 1
            sequence.append(chosen_word)
            char_count += len(chosen_word)

        return sequence
