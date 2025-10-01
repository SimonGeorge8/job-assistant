from services.gemini import GeminiService

client = GeminiService()
job_content = job_description = """Description

Ryanair Labs are currently recruiting for an API Testing QA Engineer to join Europe’s Largest Airline Group!

This is a very exciting time to join Ryanair as we look to expand our operation to 800 aircraft and 300 million guests within the next 10 years.

Ryanair Labs is the technology brand of Ryanair. Labs is a state of-the-art digital & IT innovation hub creating Europe’s Leading Travel Experience for our customers.

Here at Ryanair Labs, we’re actively building a culture where diversity and inclusion are not just words, but core principles. We’re on the lookout for dedicated professionals with disabilities who want to advance their careers. Join our innovative and dynamic team, where your skills are celebrated, and equal opportunities are guaranteed.

The Role

We are implementing the best Digital Experience Platform for Air Travel. We are looking for highly skilled API Testing Engineers who can help us build out our Automation Infrastructure to help us release in our fast paced Agile Software Development Cycle.

We are looking for individuals who have a background in development / coding but also have a strong interest in Testing in particular Automated Testing. We believe here Automation plays a big part in how we go about our Development Cycle.

Your Responsibilities Will Include

Work on a varied amount of tools and languages
Build not just Automated Tests but tools that help how our Development Team test and develop
Help us performance test with the high loads Ryanair gets daily on all our platforms
Constantly solve technical issues using your automated tests on our large systems

Requirements

1–2 years API testing experience (Karate / REST Assured / Jest)
Masters / Bachelor Degree in Computing
JavaScript

Desired Skills

AWS
Continuous integration (Jenkins)
git
SQL
Linux / Unix
Networking protocols
Atlassian application stack (Jira, Confluence, Bitbucket)

Ideal Candidates Should Be Able To Demonstrate

Enthusiasm for learning new skills and adapting quickly to new technologies
Excellent communication skills
The ability to take direction and to be able to think beyond the current set of tasks in order to effectively and fully exercise any application under test
The ability to lead/mentor more junior team members and as well as be led
Good problem definition and analysis skills as well as an ability to present issues in a way that the development team can interpret to create solutions

We Also Value (but Not Essential)

Valid disability certificate equal to or greater than 33% or recognized incapacity.

Benefits

We promote innovation, all our teams are Agile and several PoCs of new technologies or innovative ideas are launched every week.
A competitive but flexible technical career plan
We believe in an hybrid working model, you can work up to three days per week remote, but you are also going to enjoy the excellent work environment at our modern offices in the heart of Madrid.
Optional discounts on health insurances (various companies).
Travel discounts (of course!).

Competencies

Computer Skills

Teamwork

Quality"""


response = client.analyze_job_posting(job_content, "https://google.com")
s

print(response)














# from google import genai
# import os 

# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Tell me about how gemini works?"
# )

# print(response)

