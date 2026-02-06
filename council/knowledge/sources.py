"""
Public domain and freely available sources for each elder.

These URLs point to legal, freely available texts.
"""

# Sources that can be automatically fetched
PUBLIC_SOURCES = {
    "aurelius": [
        {
            "title": "Meditations - George Long Translation",
            "url": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt",
            "type": "gutenberg",
        },
    ],
    "sun_tzu": [
        {
            "title": "The Art of War - Lionel Giles Translation",
            "url": "https://www.gutenberg.org/cache/epub/132/pg132.txt",
            "type": "gutenberg",
        },
    ],
    "franklin": [
        {
            "title": "The Autobiography of Benjamin Franklin",
            "url": "https://www.gutenberg.org/cache/epub/20203/pg20203.txt",
            "type": "gutenberg",
        },
        {
            "title": "Poor Richard's Almanack",
            "url": "https://www.gutenberg.org/cache/epub/28556/pg28556.txt",
            "type": "gutenberg",
        },
        {
            "title": "The Way to Wealth",
            "url": "https://www.gutenberg.org/cache/epub/29997/pg29997.txt",
            "type": "gutenberg",
        },
    ],
    "musashi": [
        {
            "title": "The Book of Five Rings",
            "url": "https://www.gutenberg.org/cache/epub/50482/pg50482.txt",
            "type": "gutenberg",
        },
    ],
    "buddha": [
        {
            "title": "The Dhammapada - F. Max Müller Translation",
            "url": "https://www.gutenberg.org/cache/epub/2017/pg2017.txt",
            "type": "gutenberg",
        },
    ],
    "buffett": [
        # Berkshire Hathaway shareholder letters are freely available
        {
            "title": "Berkshire Hathaway Letters to Shareholders",
            "url": "https://www.berkshirehathaway.com/letters/letters.html",
            "type": "berkshire_index",
        },
    ],
    "laotzu": [
        {
            "title": "Tao Te Ching - James Legge Translation",
            "url": "https://www.gutenberg.org/cache/epub/216/pg216.txt",
            "type": "gutenberg",
        },
    ],
    "davinci": [
        {
            "title": "The Notebooks of Leonardo Da Vinci",
            "url": "https://www.gutenberg.org/cache/epub/5000/pg5000.txt",
            "type": "gutenberg",
        },
        {
            "title": "A Treatise on Painting",
            "url": "https://www.gutenberg.org/cache/epub/46915/pg46915.txt",
            "type": "gutenberg",
        },
    ],
    # Additional Stoic sources
    "seneca": [
        {
            "title": "Seneca's Morals of a Happy Life, Benefits, Anger and Clemency",
            "url": "https://www.gutenberg.org/cache/epub/56075/pg56075.txt",
            "type": "gutenberg",
        },
        {
            "title": "Minor Dialogues Together with the Dialogue on Clemency",
            "url": "https://www.gutenberg.org/cache/epub/64576/pg64576.txt",
            "type": "gutenberg",
        },
        {
            "title": "On Benefits",
            "url": "https://www.gutenberg.org/cache/epub/3794/pg3794.txt",
            "type": "gutenberg",
        },
    ],
    "epictetus": [
        {
            "title": "The Enchiridion",
            "url": "https://www.gutenberg.org/cache/epub/45109/pg45109.txt",
            "type": "gutenberg",
        },
        {
            "title": "The Golden Sayings of Epictetus",
            "url": "https://www.gutenberg.org/cache/epub/871/pg871.txt",
            "type": "gutenberg",
        },
        {
            "title": "Discourses of Epictetus",
            "url": "https://www.gutenberg.org/cache/epub/10661/pg10661.txt",
            "type": "gutenberg",
        },
    ],
    # Additional Buddhist texts
    "buddha": [
        {
            "title": "The Dhammapada - F. Max Müller Translation",
            "url": "https://www.gutenberg.org/cache/epub/2017/pg2017.txt",
            "type": "gutenberg",
        },
        {
            "title": "The Diamond Sutra",
            "url": "https://www.gutenberg.org/cache/epub/64623/pg64623.txt",
            "type": "gutenberg",
        },
        {
            "title": "The Buddha's Path of Virtue (Dhammapada - Woodward)",
            "url": "https://www.gutenberg.org/cache/epub/35185/pg35185.txt",
            "type": "gutenberg",
        },
    ],
    # Confucius (potential future elder)
    "confucius": [
        {
            "title": "The Analects of Confucius",
            "url": "https://www.gutenberg.org/cache/epub/3330/pg3330.txt",
            "type": "gutenberg",
        },
        {
            "title": "The Sayings of Confucius",
            "url": "https://www.gutenberg.org/cache/epub/46389/pg46389.txt",
            "type": "gutenberg",
        },
    ],
    # Related Daoist texts for Lao Tzu
    "chuangtzu": [
        {
            "title": "Chuang Tzu: Mystic, Moralist, and Social Reformer",
            "url": "https://www.gutenberg.org/cache/epub/59709/pg59709.txt",
            "type": "gutenberg",
        },
    ],
}

# Key excerpts to embed directly in prompts (always available, no fetching needed)
EMBEDDED_WISDOM = {
    "aurelius": """
## Key Passages from Meditations

"You have power over your mind - not outside events. Realize this, and you will find strength."

"The happiness of your life depends upon the quality of your thoughts."

"Waste no more time arguing about what a good man should be. Be one."

"When you arise in the morning think of what a privilege it is to be alive, to think, to enjoy, to love."

"The best revenge is not to be like your enemy."

"Accept the things to which fate binds you, and love the people with whom fate brings you together."

"Never value anything as profitable that compels you to break your promise, lose your self-respect, hate any man, suspect, curse, act the hypocrite, or desire anything that needs walls or curtains."

"If it is not right do not do it; if it is not true do not say it."

"Very little is needed to make a happy life; it is all within yourself in your way of thinking."

"The soul becomes dyed with the color of its thoughts."

"How much more grievous are the consequences of anger than the causes of it."

"Everything we hear is an opinion, not a fact. Everything we see is a perspective, not the truth."

"Loss is nothing else but change, and change is Nature's delight."

"The object of life is not to be on the side of the majority, but to escape finding oneself in the ranks of the insane."

"Begin each day by telling yourself: Today I shall be meeting with interference, ingratitude, insolence, disloyalty, ill-will, and selfishness."
""",

    "sun_tzu": """
## Key Passages from The Art of War

"The supreme art of war is to subdue the enemy without fighting."

"Appear weak when you are strong, and strong when you are weak."

"If you know the enemy and know yourself, you need not fear the result of a hundred battles."

"Supreme excellence consists of breaking the enemy's resistance without fighting."

"The greatest victory is that which requires no battle."

"In the midst of chaos, there is also opportunity."

"Victorious warriors win first and then go to war, while defeated warriors go to war first and then seek to win."

"Let your plans be dark and impenetrable as night, and when you move, fall like a thunderbolt."

"Strategy without tactics is the slowest route to victory. Tactics without strategy is the noise before defeat."

"There is no instance of a nation benefiting from prolonged warfare."

"The wise warrior avoids the battle."

"Know yourself and you will win all battles."

"Treat your men as you would your own beloved sons. And they will follow you into the deepest valley."

"Move swift as the Wind and closely-formed as the Wood. Attack like the Fire and be still as the Mountain."

"To know your Enemy, you must become your Enemy."

"Engage people with what they expect; it is what they are able to discern and confirms their projections."
""",

    "buddha": """
## Key Passages from the Dhammapada and Suttas

"We are what we think. All that we are arises with our thoughts. With our thoughts, we make the world."

"Peace comes from within. Do not seek it without."

"Three things cannot be long hidden: the sun, the moon, and the truth."

"You yourself, as much as anybody in the entire universe, deserve your love and affection."

"Holding onto anger is like grasping a hot coal with the intent of throwing it at someone else; you are the one who gets burned."

"In the end, only three things matter: how much you loved, how gently you lived, and how gracefully you let go of things not meant for you."

"Do not dwell in the past, do not dream of the future, concentrate the mind on the present moment."

"The trouble is, you think you have time."

"Pain is certain, suffering is optional."

"No one saves us but ourselves. No one can and no one may. We ourselves must walk the path."

"There is no path to happiness: happiness is the path."

"If you light a lamp for somebody, it will also brighten your path."

"An idea that is developed and put into action is more important than an idea that exists only as an idea."

"Work out your own salvation. Do not depend on others."

"Every morning we are born again. What we do today is what matters most."

"Nothing ever exists entirely alone; everything is in relation to everything else."
""",

    "franklin": """
## Key Passages from Benjamin Franklin

"An investment in knowledge pays the best interest."

"Early to bed and early to rise makes a man healthy, wealthy, and wise."

"By failing to prepare, you are preparing to fail."

"Tell me and I forget. Teach me and I remember. Involve me and I learn."

"Well done is better than well said."

"Energy and persistence conquer all things."

"He that is good for making excuses is seldom good for anything else."

"In this world nothing can be said to be certain, except death and taxes."

"Never leave that till tomorrow which you can do today."

"Either write something worth reading or do something worth writing."

"Lost time is never found again."

"Beware of little expenses. A small leak will sink a great ship."

"Be at war with your vices, at peace with your neighbors, and let every new year find you a better man."

"Hide not your talents. They for use were made. What's a sundial in the shade?"

"Diligence is the mother of good luck."

"When you're finished changing, you're finished."

## Franklin's Thirteen Virtues

1. TEMPERANCE: Eat not to dullness; drink not to elevation.
2. SILENCE: Speak not but what may benefit others or yourself; avoid trifling conversation.
3. ORDER: Let all your things have their places; let each part of your business have its time.
4. RESOLUTION: Resolve to perform what you ought; perform without fail what you resolve.
5. FRUGALITY: Make no expense but to do good to others or yourself; i.e., waste nothing.
6. INDUSTRY: Lose no time; be always employ'd in something useful; cut off all unnecessary actions.
7. SINCERITY: Use no hurtful deceit; think innocently and justly, and, if you speak, speak accordingly.
8. JUSTICE: Wrong none by doing injuries, or omitting the benefits that are your duty.
9. MODERATION: Avoid extremes; forbear resenting injuries so much as you think they deserve.
10. CLEANLINESS: Tolerate no uncleanliness in body, clothes, or habitation.
11. TRANQUILLITY: Be not disturbed at trifles, or at accidents common or unavoidable.
12. CHASTITY: Rarely use venery but for health or offspring, never to dullness, weakness, or the injury of your own or another's peace or reputation.
13. HUMILITY: Imitate Jesus and Socrates.
""",

    "musashi": """
## Key Passages from The Book of Five Rings

"There is nothing outside of yourself that can ever enable you to get better, stronger, richer, quicker, or smarter. Everything is within. Everything exists. Seek nothing outside of yourself."

"You must understand that there is more than one path to the top of the mountain."

"Do not regret what you have done."

"Think lightly of yourself and deeply of the world."

"The ultimate aim of martial arts is not having to use them."

"Do nothing that is of no use."

"Perceive that which cannot be seen with the eye."

"Get beyond love and grief: exist for the good of Man."

"It is difficult to understand the universe if you only study one planet."

"In battle, if you make your opponent flinch, you have already won."

"The only reason a warrior is alive is to fight, and the only reason a warrior fights is to win."

"You can only fight the way you practice."

"Today is victory over yourself of yesterday; tomorrow is your victory over lesser men."

"Step by step walk the thousand-mile road."

"If you wish to control others you must first control yourself."

"All man are the same except for their belief in their own selves, regardless of what others may think of them."

## The Dokkodo (The Way of Walking Alone)

1. Accept everything just the way it is.
2. Do not seek pleasure for its own sake.
3. Do not, under any circumstances, depend on a partial feeling.
4. Think lightly of yourself and deeply of the world.
5. Be detached from desire your whole life.
6. Do not regret what you have done.
7. Never be jealous.
8. Never let yourself be saddened by a separation.
9. Resentment and complaint are appropriate neither for oneself nor others.
10. Do not let yourself be guided by the feeling of lust or love.
11. In all things have no preferences.
12. Be indifferent to where you live.
13. Do not pursue the taste of good food.
14. Do not hold on to possessions you no longer need.
15. Do not act following customary beliefs.
16. Do not collect weapons or practice with weapons beyond what is useful.
17. Do not fear death.
18. Do not seek to possess either goods or fiefs for your old age.
19. Respect Buddha and the gods without counting on their help.
20. You may abandon your own body but you must preserve your honor.
21. Never stray from the way.
""",

    "munger": """
## Key Wisdom from Charlie Munger

"Invert, always invert: Turn a situation or problem upside down. Look at it backward."

"Show me the incentive and I will show you the outcome."

"I never allow myself to have an opinion on anything that I don't know the other side's argument better than they do."

"Spend each day trying to be a little wiser than you were when you woke up."

"The best thing a human being can do is to help another human being know more."

"In my whole life, I have known no wise people who didn't read all the time – none, zero."

"It is remarkable how much long-term advantage people like us have gotten by trying to be consistently not stupid, instead of trying to be very intelligent."

"You don't have to be brilliant, only a little bit wiser than the other guys, on average, for a long, long time."

"The big money is not in the buying and selling, but in the waiting."

"Acknowledging what you don't know is the dawning of wisdom."

"The iron rule of nature is: you get what you reward for. If you want ants to come, you put sugar on the floor."

"Take a simple idea and take it seriously."

"A great business at a fair price is superior to a fair business at a great price."

"The safest way to get what you want is to deserve what you want."

"Mimicking the herd invites regression to the mean."

"You must know the big ideas in the big disciplines and use them routinely – all of them, not just a few."

## Munger's Mental Models

1. Inversion - Think about what you want to avoid
2. Circle of Competence - Know what you don't know
3. First Principles Thinking - Break down problems to fundamentals
4. Thought Experiment - Imagine outcomes
5. Second-Order Thinking - Consider the consequences of consequences
6. Probabilistic Thinking - Consider likely outcomes
7. Occam's Razor - Simple explanations are preferable
8. Hanlon's Razor - Don't attribute to malice what can be explained by stupidity
9. Opportunity Cost - What are you giving up?
10. Margin of Safety - Leave room for error
""",

    "buffett": """
## Key Wisdom from Warren Buffett

"Rule No. 1: Never lose money. Rule No. 2: Never forget Rule No. 1."

"Be fearful when others are greedy, and greedy when others are fearful."

"Price is what you pay. Value is what you get."

"It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price."

"The most important thing to do if you find yourself in a hole is to stop digging."

"Someone's sitting in the shade today because someone planted a tree a long time ago."

"Risk comes from not knowing what you're doing."

"In the business world, the rearview mirror is always clearer than the windshield."

"Chains of habit are too light to be felt until they are too heavy to be broken."

"It takes 20 years to build a reputation and five minutes to ruin it. If you think about that, you'll do things differently."

"The difference between successful people and really successful people is that really successful people say no to almost everything."

"Only when the tide goes out do you discover who's been swimming naked."

"Time is the friend of the wonderful company, the enemy of the mediocre."

"I will tell you how to become rich. Close the doors. Be fearful when others are greedy. Be greedy when others are fearful."

"The stock market is a device for transferring money from the impatient to the patient."

"Our favorite holding period is forever."

"Never invest in a business you cannot understand."

"Diversification is protection against ignorance. It makes little sense if you know what you are doing."

"If you aren't thinking about owning a stock for 10 years, don't even think about owning it for 10 minutes."
""",

    "bruce_lee": """
## Key Wisdom from Bruce Lee

"Be water, my friend. Empty your mind. Be formless, shapeless, like water."

"Absorb what is useful, discard what is useless and add what is specifically your own."

"I fear not the man who has practiced 10,000 kicks once, but I fear the man who has practiced one kick 10,000 times."

"The key to immortality is first living a life worth remembering."

"Knowing is not enough, we must apply. Willing is not enough, we must do."

"If you always put limits on everything you do, physical or anything else, it will spread into your work and into your life. There are no limits. There are only plateaus."

"Do not pray for an easy life; pray for the strength to endure a difficult one."

"Mistakes are always forgivable, if one has the courage to admit them."

"A wise man can learn more from a foolish question than a fool can learn from a wise answer."

"To hell with circumstances; I create opportunities."

"The successful warrior is the average man, with laser-like focus."

"Adapt what is useful, reject what is useless, and add what is specifically your own."

"Using no way as way, having no limitation as limitation."

"A goal is not always meant to be reached; it often serves simply as something to aim at."

"Real living is living for others."

"Don't fear failure. Not failure, but low aim, is the crime. In great attempts it is glorious even to fail."

"If you spend too much time thinking about a thing, you'll never get it done."

"Simplicity is the key to brilliance."

"The more we value things, the less we value ourselves."
""",

    "branden": """
## Key Wisdom from Nathaniel Branden

"The first step toward change is awareness. The second step is acceptance."

"No one is coming. No one is coming to save you. Your life is entirely your responsibility."

"Self-esteem is the reputation we acquire with ourselves."

"The greatest crime we commit against ourselves is not that we deny our shortcomings but that we deny our greatness."

"Live consciously. Ask yourself: What am I avoiding facing?"

"There is overwhelming evidence that the higher the level of self-esteem, the more likely one will be to treat others with respect, kindness, and generosity."

"Of all the judgments we pass in life, none is more important than the judgment we pass on ourselves."

"The tragedy is that so many people look for self-confidence and self-respect everywhere except within themselves."

"How do we nurture self-esteem? By practicing the six pillars."

"The greatest barrier to achievement and success is not lack of talent or ability but, rather, the fact that achievement and success, above a certain level, are outside our self-concept."

"Self-acceptance is my refusal to be in an adversarial relationship to myself."

"We tend to feel most comfortable, 'most at home,' with people whose self-esteem level resembles our own."

"A commitment to awareness and continuous learning must be practiced as a way of life."

"Taking responsibility - practicing self-responsibility - means not asking 'Who's to blame?' but 'What needs to be done?'"

## The Six Pillars of Self-Esteem

1. The Practice of Living Consciously
2. The Practice of Self-Acceptance
3. The Practice of Self-Responsibility
4. The Practice of Self-Assertiveness
5. The Practice of Living Purposefully
6. The Practice of Personal Integrity
""",

    "peterson": """
## Key Wisdom from Jordan Peterson

"Set your house in perfect order before you criticize the world."

"Compare yourself to who you were yesterday, not to who someone else is today."

"Pursue what is meaningful, not what is expedient."

"You're not as fragile as you think, and you can handle way more than you believe."

"If you can't even clean up your own room, who are you to give advice to the world?"

"The purpose of life is finding the largest burden that you can bear and bearing it."

"You should be a monster, an absolute monster, and then learn to control it."

"Tell the truth, or at least don't lie."

"To stand up straight with your shoulders back is to accept the terrible responsibility of life, with eyes wide open."

"It's in responsibility that most people find the meaning that sustains them through life."

"If you fulfill your obligations every day, you don't need to worry about the future."

"When you have something to say, silence is a lie."

"You cannot be protected from the things that frighten you and hurt you, but if you identify with the part of your being that is responsible for transformation, then you are always the equal, or more than the equal of the things that frighten you."

"The way that you make people resilient is by voluntarily exposing them to things that they are afraid of and that make them uncomfortable."

"What you aim at determines what you see."

"You must determine where you are going in your life, because you cannot get there unless you move in that direction."

"Life is suffering. That's clear. There is no more basic, irrefutable truth."

"Act so that you can tell the truth about how you act."

## 12 Rules for Life (Summary)

1. Stand up straight with your shoulders back
2. Treat yourself like someone you are responsible for helping
3. Make friends with people who want the best for you
4. Compare yourself to who you were yesterday, not to who someone else is today
5. Do not let your children do anything that makes you dislike them
6. Set your house in perfect order before you criticize the world
7. Pursue what is meaningful, not what is expedient
8. Tell the truth – or, at least, don't lie
9. Assume that the person you are listening to might know something you don't
10. Be precise in your speech
11. Do not bother children when they are skateboarding
12. Pet a cat when you encounter one on the street
""",

    "clear": """
## Key Wisdom from James Clear

"You do not rise to the level of your goals. You fall to the level of your systems."

"Every action is a vote for the type of person you wish to become."

"Habits are the compound interest of self-improvement."

"The most practical way to change who you are is to change what you do."

"You should be far more concerned with your current trajectory than with your current results."

"Be the designer of your world and not merely the consumer of it."

"Time magnifies the margin between success and failure. It will multiply whatever you feed it."

"Goals are good for setting a direction, but systems are best for making progress."

"The ultimate form of intrinsic motivation is when a habit becomes part of your identity."

"Success is the product of daily habits—not once-in-a-lifetime transformations."

"Getting 1 percent better every day counts for a lot in the long-run."

"Changes that seem small and unimportant at first will compound into remarkable results if you're willing to stick with them for years."

"All big things come from small beginnings. The seed of every habit is a single, tiny decision."

"When you fall in love with the process rather than the product, you don't have to wait to give yourself permission to be happy."

"The greatest threat to success is not failure but boredom."

"Professionals stick to the schedule; amateurs let life get in the way."

"Missing once is an accident. Missing twice is the start of a new habit."

## The Four Laws of Behavior Change

To build a good habit:
1. Make it obvious (Cue)
2. Make it attractive (Craving)
3. Make it easy (Response)
4. Make it satisfying (Reward)

To break a bad habit:
1. Make it invisible
2. Make it unattractive
3. Make it difficult
4. Make it unsatisfying

## Key Concepts from Atomic Habits

**Habit Stacking**: "After I [CURRENT HABIT], I will [NEW HABIT]."

**The Two-Minute Rule**: When you start a new habit, it should take less than two minutes to do.

**Environment Design**: Make the cues of good habits obvious and the cues of bad habits invisible.

**Temptation Bundling**: Link an action you want to do with an action you need to do.

**Implementation Intentions**: "I will [BEHAVIOR] at [TIME] in [LOCATION]."

**Identity-Based Habits**: Focus on who you wish to become, not what you want to achieve.

**The Plateau of Latent Potential**: Your work is not wasted; it is just being stored. The breakthrough will come.

**Decisive Moments**: Each day is made up of many moments, but it is really a few habitual choices that determine the path you take.
""",

    "greene": """
## Key Wisdom from Robert Greene

"The future belongs to those who learn more skills and combine them in creative ways."

"Never waste valuable time, or mental peace of mind, on the affairs of others."

"When you show yourself to the world and display your talents, you naturally stir all kinds of resentment, envy, and other manifestations of insecurity."

"Do not leave your reputation to chance or gossip; it is your life's artwork, and you must craft it, hone it, and display it with the care of an artist."

"Never be distracted by people's glamorous portraits of themselves and their lives; search and dig for what really imprisons them."

"Mastery is not a function of genius or talent. It is a function of time and intense focus applied to a particular field of knowledge."

"The time that leads to mastery is dependent on the intensity of our focus."

"Think of it this way: There are two kinds of time in our lives: dead time, when people are passive and waiting, and alive time, when people are learning and acting."

"The key to power is the ability to judge who is best able to further your interests in all situations."

"When you meet a swordsman, draw your sword: Do not recite poetry to one who is not a poet."

## The 48 Laws of Power (Selected)

Law 1: Never Outshine the Master
Law 3: Conceal Your Intentions
Law 4: Always Say Less Than Necessary
Law 6: Court Attention at All Costs
Law 15: Crush Your Enemy Totally
Law 16: Use Absence to Increase Respect and Honor
Law 25: Re-Create Yourself
Law 28: Enter Action with Boldness
Law 29: Plan All the Way to the End
Law 33: Discover Each Man's Thumbscrew
Law 35: Master the Art of Timing
Law 48: Assume Formlessness
""",

    "naval": """
## Key Wisdom from Naval Ravikant

"Seek wealth, not money or status. Wealth is having assets that earn while you sleep."

"Arm yourself with specific knowledge, accountability, and leverage."

"Specific knowledge is knowledge that you cannot be trained for. If society can train you, it can train someone else, and replace you."

"Learn to sell. Learn to build. If you can do both, you will be unstoppable."

"Reading is faster than listening. Doing is faster than watching."

"The most important skill for getting rich is becoming a perpetual learner."

"If you can't code, write books and blogs, record videos and podcasts."

"There are no get rich quick schemes. That's just someone else getting rich off you."

"You're not going to get rich renting out your time. You must own equity - a piece of a business - to gain your financial freedom."

"Play iterated games. All the returns in life, whether in wealth, relationships, or knowledge, come from compound interest."

"Pick business partners with high intelligence, energy, and, above all, integrity."

"A calm mind, a fit body, and a house full of love. These things cannot be bought. They must be earned."

"Desire is a contract you make with yourself to be unhappy until you get what you want."

"Happiness is a skill that can be learned."

"The three big ones in life are wealth, health, and happiness. We pursue them in that order, but their importance is reverse."
""",

    "rubin": """
## Key Wisdom from Rick Rubin

"The goal is not to do what you can do. It's to do what you can't yet do."

"Nothing is more important than the work being great."

"Art is a conversation with the unconscious."

"Rules are there to understand, then to transcend."

"Great art comes from removing, not adding."

"The best work comes from being present, not from trying."

"Trust the process more than the product."

"Create your work in a bubble. Share it with the world when you're ready."

"Living life as an artist is a practice. You are either engaging in the practice or you're not."

"The audience comes last. You are first."

"If you have an idea you're excited about and you don't bring it to life, it's not uncommon for the idea to find its voice through another maker."

"Look for what you notice but no one else sees."

"The sensitivity that allows us to be great artists is the same sensitivity that makes life challenging."

"Creativity has nothing to do with any activity. Creativity is a way of operating."

"Cleaning up your field of vision allows new things to emerge."
""",

    "oprah": """
## Key Wisdom from Oprah Winfrey

"The biggest adventure you can take is to live the life of your dreams."

"Turn your wounds into wisdom."

"You get in life what you have the courage to ask for."

"Be thankful for what you have; you'll end up having more."

"The more you praise and celebrate your life, the more there is in life to celebrate."

"Surround yourself with only people who are going to lift you higher."

"Doing the best at this moment puts you in the best place for the next moment."

"Think like a queen. A queen is not afraid to fail. Failure is another stepping stone to greatness."

"Lots of people want to ride with you in the limo, but what you want is someone who will take the bus with you when the limo breaks down."

"The whole point of being alive is to evolve into the complete person you were intended to be."

"You teach people how to treat you."

"Passion is energy. Feel the power that comes from focusing on what excites you."

"Real integrity is doing the right thing, knowing that nobody's going to know whether you did it or not."

"What I know for sure is that speaking your truth is the most powerful tool we all have."

"The greatest discovery of all time is that a person can change their future by merely changing their attitude."
""",

    "thich": """
## Key Wisdom from Thich Nhat Hanh

"Breathing in, I calm body and mind. Breathing out, I smile."

"Walk as if you are kissing the Earth with your feet."

"Present moment, wonderful moment."

"No mud, no lotus."

"The seed of suffering in you may be strong, but don't wait until there is no more suffering to allow yourself to be happy."

"Because you are alive, everything is possible."

"Smile, breathe, and go slowly."

"Understanding is love's other name."

"When another person makes you suffer, it is because he suffers deeply within himself, and his suffering is spilling over."

"People have a hard time letting go of their suffering. Out of a fear of the unknown, they prefer suffering that is familiar."

"To be beautiful means to be yourself. You don't need to be accepted by others. You need to accept yourself."

"Many people think excitement is happiness. But when you are excited you are not peaceful. True happiness is based on peace."

"Feelings come and go like clouds in a windy sky. Conscious breathing is my anchor."

"If you love someone but rarely make yourself available to him or her, that is not true love."

"Life can be found only in the present moment. The past is gone, the future is not yet here."

"Waking up this morning, I smile. Twenty-four brand new hours are before me."

"Letting go gives us freedom, and freedom is the only condition for happiness."
""",

    "jung": """
## Key Wisdom from Carl Jung

"Until you make the unconscious conscious, it will direct your life and you will call it fate."

"One does not become enlightened by imagining figures of light, but by making the darkness conscious."

"What you resist, persists."

"I am not what happened to me, I am what I choose to become."

"The meeting of two personalities is like the contact of two chemical substances: if there is any reaction, both are transformed."

"Your visions will become clear only when you can look into your own heart. Who looks outside, dreams; who looks inside, awakes."

"The privilege of a lifetime is to become who you truly are."

"The pendulum of the mind oscillates between sense and nonsense, not between right and wrong."

"Every form of addiction is bad, no matter whether the narcotic be alcohol, morphine, or idealism."

"Knowing your own darkness is the best method for dealing with the darknesses of other people."

"Everything that irritates us about others can lead us to an understanding of ourselves."

"Loneliness does not come from having no people about one, but from being unable to communicate the things that seem important to oneself."

"The shoe that fits one person pinches another; there is no recipe for living that suits all cases."

"We cannot change anything unless we accept it."

"People will do anything, no matter how absurd, to avoid facing their own souls."

"In all chaos there is a cosmos, in all disorder a secret order."

## Key Jungian Concepts

**The Shadow**: The unconscious aspect of the personality which the ego does not identify with.

**Archetypes**: Universal, archaic patterns and images that derive from the collective unconscious.

**Individuation**: The process of psychological integration, of becoming whole.

**Anima/Animus**: The unconscious feminine side of a man / masculine side of a woman.

**The Self**: The archetype of wholeness and the regulating center of the psyche.

**Synchronicity**: Meaningful coincidences with no causal relationship.

**Collective Unconscious**: Inherited potentials activated by personal experience.
""",

    "kabatzinn": """
## Key Wisdom from Jon Kabat-Zinn

"You can't stop the waves, but you can learn to surf."

"Mindfulness is awareness that arises through paying attention, on purpose, in the present moment, non-judgmentally."

"The little things? The little moments? They aren't little."

"Wherever you go, there you are."

"The best way to capture moments is to pay attention. This is how we cultivate mindfulness."

"Almost everything will work again if you unplug it for a few minutes, including you."

"In Asian languages, the word for 'mind' and the word for 'heart' are the same. So if you're not hearing mindfulness in some deep way as heartfulness, you're not really understanding it."

"We take care of the future best by taking care of the present now."

"Patience is a form of wisdom. It demonstrates that we understand and accept the fact that sometimes things must unfold in their own time."

"The present moment is filled with joy and happiness. If you are attentive, you will see it."

"Meditation is the only intentional, systematic human activity which at bottom is about not trying to improve yourself or get anywhere else."

"Life only unfolds in moments. The healing power of mindfulness lies in living each of those moments as fully as we can."

"Perhaps the most 'spiritual' thing any of us can do is simply to look through our own eyes, see with eyes of wholeness, and act with integrity and kindness."

## MBSR Foundations

**The Body Scan**: Systematic attention to sensations throughout the body.

**Sitting Meditation**: Awareness of breath, body, sounds, thoughts, and choiceless awareness.

**Mindful Movement**: Yoga and walking meditation with full presence.

**Informal Practice**: Bringing mindfulness to everyday activities.

**Non-Judging**: Observing experience without evaluating it as good or bad.

**Beginner's Mind**: Approaching each moment as if for the first time.

**Non-Striving**: Not trying to get anywhere or achieve any particular state.
""",

    "laotzu": """
## Key Passages from the Tao Te Ching

"The Tao that can be told is not the eternal Tao. The name that can be named is not the eternal name."

"When you are content to be simply yourself and don't compare or compete, everyone will respect you."

"Nature does not hurry, yet everything is accomplished."

"A journey of a thousand miles begins with a single step."

"Knowing others is intelligence; knowing yourself is true wisdom. Mastering others is strength; mastering yourself is true power."

"When I let go of what I am, I become what I might be."

"The wise man is one who knows what he does not know."

"Do the difficult things while they are easy and do the great things while they are small."

"Be content with what you have; rejoice in the way things are. When you realize there is nothing lacking, the whole world belongs to you."

"If you do not change direction, you may end up where you are heading."

"He who conquers others is strong; he who conquers himself is mighty."

"Simplicity, patience, compassion. These three are your greatest treasures."

"The softest things in the world overcome the hardest things in the world."

"To lead people, walk behind them."

"Those who know do not speak. Those who speak do not know."

"Act without expectation."

"In dwelling, live close to the ground. In thinking, keep to the simple. In conflict, be fair and generous. In governing, don't try to control. In work, do what you enjoy. In family life, be completely present."

## Key Taoist Concepts

**Wu Wei**: Non-action, or effortless action. Going with the natural flow.

**Te**: Virtue or power that comes from alignment with the Tao.

**Pu**: The uncarved block. Simplicity and original nature.

**Yin and Yang**: Complementary opposites in dynamic balance.
""",

    "davinci": """
## Key Wisdom from Leonardo da Vinci

"Simplicity is the ultimate sophistication."

"Learning never exhausts the mind."

"The noblest pleasure is the joy of understanding."

"It had long since come to my attention that people of accomplishment rarely sat back and let things happen to them. They went out and happened to things."

"I have been impressed with the urgency of doing. Knowing is not enough; we must apply. Being willing is not enough; we must do."

"Study without desire spoils the memory, and it retains nothing that it takes in."

"The greatest deception men suffer is from their own opinions."

"Time stays long enough for anyone who will use it."

"Art is never finished, only abandoned."

"Experience does not err. Only your judgments err by expecting from her what is not in her power."

"Iron rusts from disuse; water loses its purity from stagnation... even so does inaction sap the vigor of the mind."

"Nature is the source of all true knowledge. She has her own logic, her own laws, she has no effect without cause nor invention without necessity."

"There are three classes of people: those who see, those who see when they are shown, those who do not see."

"I love those who can smile in trouble, who can gather strength from distress, and grow brave by reflection."

"Obstacles cannot crush me. Every obstacle yields to stern resolve."

"The painter has the Universe in his mind and hands."

## Leonardo's Principles

**Curiosità**: An insatiably curious approach to life and unrelenting quest for continuous learning.

**Dimostrazione**: A commitment to test knowledge through experience.

**Sensazione**: The continual refinement of the senses as the means to enliven experience.

**Sfumato**: A willingness to embrace ambiguity, paradox, and uncertainty.

**Arte/Scienza**: The development of the balance between science and art, logic and imagination.

**Corporalità**: The cultivation of grace, fitness, and poise.

**Connessione**: A recognition of and appreciation for the interconnectedness of all things.
""",

    "kahneman": """
## Key Wisdom from Daniel Kahneman

"Nothing in life is as important as you think it is, while you are thinking about it."

"A reliable way to make people believe in falsehoods is frequent repetition, because familiarity is not easily distinguished from truth."

"We can be blind to the obvious, and we are also blind to our blindness."

"The confidence that individuals have in their beliefs depends mostly on the quality of the story they can tell about what they see."

"Our comforting conviction that the world makes sense rests on a secure foundation: our almost unlimited ability to ignore our ignorance."

"We are prone to overestimate how much we understand about the world and to underestimate the role of chance in events."

"The easiest way to increase happiness is to control your use of time."

"Intelligence is not only the ability to reason; it is also the ability to find relevant material in memory and to deploy attention when needed."

"Loss aversion is a powerful conservative force that favors minimal changes from the status quo."

"The planning fallacy is the tendency to underestimate the time, costs, and risks of future actions."

"What you see is all there is." (WYSIATI)

"Intuition is nothing more and nothing less than recognition."

## System 1 and System 2

**System 1**: Fast, automatic, emotional, stereotypic, unconscious. Operates effortlessly.

**System 2**: Slow, effortful, logical, calculating, conscious. Requires attention.

## Key Biases and Heuristics

**Anchoring**: Relying too heavily on the first piece of information encountered.

**Availability Heuristic**: Judging probability by how easily examples come to mind.

**Representativeness**: Judging probability by similarity to stereotypes.

**Loss Aversion**: Losses loom larger than gains (roughly 2:1).

**Overconfidence**: Systematic tendency to overestimate the accuracy of our beliefs.

**Hindsight Bias**: "I knew it all along" after learning an outcome.
""",

    "tubman": """
## Key Wisdom from Harriet Tubman

"Every great dream begins with a dreamer. Always remember, you have within you the strength, the patience, and the passion to reach for the stars to change the world."

"I freed a thousand slaves. I could have freed a thousand more if only they knew they were slaves."

"I had reasoned this out in my mind; there was one of two things I had a right to, liberty or death; if I could not have one, I would have the other."

"I was the conductor of the Underground Railroad for eight years, and I can say what most conductors can't say—I never ran my train off the track and I never lost a passenger."

"If you hear the dogs, keep going. If you see the torches in the woods, keep going. If there's shouting after you, keep going. Don't ever stop. Keep going. If you want a taste of freedom, keep going."

"I grew up like a neglected weed—ignorant of liberty, having no experience of it."

"Lord, I'm going to hold steady on to You and You've got to see me through."

"I never met any person of any color who had more confidence in the voice of God."

"I looked at my hands to see if I was the same person. There was such a glory over everything."

"Quakers almost as good as colored. They call themselves friends and you can trust them every time."

## Tubman's Leadership Principles

**Faith**: Unwavering trust in divine guidance and purpose.

**Courage**: Acting despite fear, not in the absence of it.

**Preparation**: Meticulous planning and knowledge of the terrain.

**Adaptability**: Changing routes and methods as circumstances required.

**Resolve**: Never turning back, never giving up.

**Service**: Dedicating her freedom to freeing others.
""",

    "tetlock": """
## Key Wisdom from Philip Tetlock

"The fox knows many things, but the hedgehog knows one big thing."

"Beliefs are hypotheses to be tested, not treasures to be protected."

"The key to being a superforecaster is perpetual beta—the mindset of always testing and refining your beliefs."

"Superforecasters are not brilliant. They are tenacious and have an appetite for evidence."

"Good judgment requires you to think about what might be and not just what is."

"Forecasting is not about predicting the unpredictable but about being less wrong over time."

"The single most important factor in good forecasting is trying hard."

"Overconfidence is the mother of all psychological biases."

"Good forecasters tend to be actively open-minded."

"Break problems into components. Distinguish knowable from unknowable."

"The goal is not to be right but to be calibrated—knowing what you know and don't know."

## Superforecasting Principles

**Triage**: Focus on questions that are neither too easy nor too hard to answer.

**Break Down Problems**: Fermi-ize complex questions into tractable sub-questions.

**Strike the Right Balance**: Weight inside and outside views appropriately.

**Update Incrementally**: Adjust beliefs in response to new evidence, but don't overreact.

**Look for Clashing Causal Forces**: Consider what pushes toward and against outcomes.

**Distinguish As Many Degrees of Uncertainty**: Fine-grained probability estimates.

**Strike Balance Between Under- and Over-Confidence**: Humility about uncertainty.

**Look for Errors Behind Your Mistakes**: Conduct postmortems on predictions.

**Bring Out the Best in Others**: Harness collective wisdom through teams.

**Master the Skill-Luck Balance**: Understand the role of chance in outcomes.
""",

    "klein": """
## Key Wisdom from Gary Klein

"Intuition is the way we translate our experience into action."

"The power of intuition lies in the stories we build up over time."

"Experts see the world differently than novices. They notice things others miss."

"Recognition-primed decision making: In familiar situations, experienced decision makers recognize patterns and act accordingly."

"In complex, time-pressured situations, the first option that comes to mind is usually the best option."

"Analytical methods work well in laboratories but often fail in the field."

"The pre-mortem: Imagine the project has failed. Now explain why."

"Insight is the unexpected shift to a better story."

"Experts don't make decisions by comparing options. They assess the situation and respond."

"The real problem with novices isn't that they think slow—it's that they see less."

## Naturalistic Decision Making Principles

**Recognition-Primed Decision Making (RPD)**: Experienced decision makers recognize situations as typical cases and rapidly identify an appropriate response.

**Mental Simulation**: Running through a course of action in your mind to see if it will work.

**Leverage Points**: Finding the key factor that makes the biggest difference.

**The Pre-Mortem**: Before starting a project, imagine it has failed and explain why.

**Satisficing**: Finding a good enough option quickly rather than optimizing.

**Situation Assessment**: Understanding the situation is more important than comparing options.

## Sources of Power

- Pattern recognition
- Mental simulation
- Leverage points
- Seeing the invisible
- Story building
- Noticing anomalies
""",

    "meadows": """
## Key Wisdom from Donella Meadows

"We can't control systems or figure them out. But we can dance with them."

"A system is a set of things—people, cells, molecules, or whatever—interconnected in such a way that they produce their own pattern of behavior over time."

"The behavior of a system cannot be known just by knowing the elements of which the system is made."

"Systems thinking is a discipline for seeing wholes."

"The least obvious part of the system, its function or purpose, is often the most crucial determinant of the system's behavior."

"Pay attention to what is important, not just what is quantifiable."

"Leverage points are places within a complex system where a small shift in one thing can produce big changes in everything else."

"The systems-Loss of information creates the illusion that what we can see is all there is to see."

"Growth in a finite world can only be sustained for so long."

"Missing information flows is one of the most common causes of system malfunction."

## Leverage Points to Intervene in a System (in increasing order of effectiveness)

12. Constants, parameters, numbers
11. The sizes of buffers and stabilizing stocks
10. The structure of material stocks and flows
9. The lengths of delays
8. The strength of negative feedback loops
7. The gain around driving positive feedback loops
6. The structure of information flows
5. The rules of the system
4. The power to add, change, evolve, or self-organize system structure
3. The goals of the system
2. The mindset or paradigm out of which the system arises
1. The power to transcend paradigms

## Key Systems Concepts

**Feedback Loops**: Balancing (negative) and reinforcing (positive) loops drive system behavior.

**Stocks and Flows**: Accumulations and the rates of change that affect them.

**Delays**: Time lags between action and response.

**Bounded Rationality**: People make reasonable decisions based on limited information.
""",

    "hannibal": """
## Key Wisdom Attributed to Hannibal Barca

"We will either find a way, or make one."

"I will use fire and steel to arrest the destiny of Rome."

"The mirrors in your mind can reflect the best of yourself, not the worst of someone else."

"God has given to man no sharper spur to victory than contempt of death."

"Many things which nature makes difficult become easy to the man who uses his brains."

## Hannibal's Strategic Principles

**Audacity**: Cross the Alps when everyone says it's impossible. The unexpected route is often the best route.

**Adaptability**: Use the enemy's strengths against them. Turn elephants into weapons, turn cavalry into hammer and anvil.

**Intelligence Gathering**: Know your enemy—their leaders, their weaknesses, their divisions. Exploit them all.

**Psychological Warfare**: Victory is won in the mind before the battle. Demoralize, confuse, and terrorize.

**Speed and Mobility**: Strike before they can prepare. Concentration of force at the decisive point.

**Alliance Building**: Unite disparate peoples against a common enemy. The enemy of my enemy is my friend.

## Battle of Cannae Principles

**Double Envelopment**: The classic tactical masterpiece—weak center, strong flanks.

**Use of Terrain**: Position yourself where the enemy cannot use their numbers.

**Flexibility of Command**: Commanders must adapt to circumstances, not rigidly follow plans.

**Concentration of Force**: Mass strength where the enemy is weakest.

**Decisive Engagement**: When you strike, strike to destroy, not merely to defeat.
""",

    "boudicca": """
## Wisdom and Words Attributed to Boudicca

"It is not as a woman descended from noble ancestry, but as one of the people that I am avenging lost freedom."

"Win the battle or perish: that is what I, a woman, will do—let the men live in slavery if they will."

"Nothing is safe from Roman pride and arrogance. They will deface the sacred and deflower our virgins."

"On this spot we must either conquer, or die with glory. There is no alternative."

"I am not fighting for my kingdom and wealth now. I am fighting as an ordinary person for my lost freedom, my bruised body, and my outraged daughters."

## Boudicca's Leadership Principles

**Righteous Anger**: Transform injustice into fuel for resistance. Let outrage become action.

**Unity**: Bring together tribes that once competed. A common enemy creates common purpose.

**Leading from the Front**: A leader who shares the danger earns the devotion of warriors.

**Total Commitment**: There is no negotiation with tyranny. Freedom or death.

**Symbolic Power**: The queen in the chariot—an image that rallies thousands.

**Inspiring Speech**: Words can move armies. Speak to the heart of what people have lost.

## Strategic Lessons from the Iceni Revolt

- Strike when the enemy is dispersed
- Target symbols of oppression
- Move faster than the enemy can respond
- Inspire through personal example
- Know when the time is right
- Accept that some battles must be fought regardless of odds
""",

    "genghis": """
## Key Wisdom Attributed to Genghis Khan

"I am the punishment of God. If you had not committed great sins, God would not have sent a punishment like me upon you."

"The greatest happiness is to scatter your enemy, to drive him before you, to see his cities reduced to ashes."

"If you're afraid, don't do it. If you're doing it, don't be afraid."

"It is not sufficient that I succeed—all others must fail."

"One arrow alone can be easily broken, but many arrows are indestructible."

"A leader can never be happy until his people are happy."

"An action committed in anger is an action doomed to failure."

"With Heaven's aid I have conquered for you a huge empire. But my life was too short to achieve the conquest of the world."

"The strength of a wall is neither greater nor less than the courage of the men who defend it."

"Remember, you have no companions but your shadow."

## Genghis Khan's Leadership Principles

**Meritocracy**: Promote based on ability, not birth. Loyalty and competence above bloodline.

**Information Superiority**: Know everything about your enemy before you strike. Spies and scouts are worth more than armies.

**Adaptability**: Adopt the best practices of conquered peoples. Innovation through integration.

**Psychological Warfare**: Reputation as a weapon. Fear conquers cities before your army arrives.

**Discipline**: Absolute loyalty to the command structure. Desertion is death.

**Delegation**: Trust capable commanders with independence. Coordinate goals, not methods.

**Total War**: No half measures. Complete victory or nothing.

## Military Innovations

- Combined arms cavalry tactics
- Decimal organization of armies
- Coordinated movements across vast distances
- Intelligence networks spanning continents
- Integration of siege technology from conquered peoples
""",

    "lauder": """
## Key Wisdom from Estée Lauder

"I have never worked a day in my life without selling. If I believe in something, I sell it, and I sell it hard."

"I didn't get here by dreaming about it or thinking about it—I got here by doing it."

"All great things began as dreams. There is always someone who, if they have the dream, will make it come true."

"Look for a sweet person and everything else will follow."

"Touch your customer and you're halfway there."

"Risk-taking is the cornerstone of empires."

"I never dreamed about success. I worked for it."

"When you stop talking, you've lost your customer. When you turn your back, you've lost her."

"If you don't sell, it's not the product that's wrong, it's you."

"Beauty is an attitude. There's no secret. Why are all brides beautiful? Because on their wedding day they care about how they look."

"Telephone, telegraph, tell a woman."

"I made mistakes. I admitted them. But above all, I learned from them."

## Estée Lauder's Business Principles

**Personal Touch**: The gift with purchase. The sample. The hand-to-hand selling.

**Quality Obsession**: Never compromise on the product. Your name is on it.

**Persistence**: "No" is just the beginning of the conversation.

**Customer Intimacy**: Know your customer. Touch her. Talk to her. Understand her.

**Word of Mouth**: One satisfied customer tells five friends.

**Elegant Presentation**: The packaging is part of the product. Luxury is in the details.

**Dream Selling**: You don't sell cream—you sell hope, beauty, transformation.

**Leading by Example**: Be the embodiment of what you sell. Represent the dream.
""",
}
