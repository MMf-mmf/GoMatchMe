# Plateias


# TODAY SEP 3 2023
- CREATE A URL VIEW AND FORM FOR BASIC PROFILE FORM SUBMISSION
- ADD ALL FIELDS TO THE FORM

  






# implement captcha on all forms
- https://django-simple-captcha.readthedocs.io/en/latest/advanced.html


  - [] request a refund
  - [] add a suggestion and take payment minimum $2
  - [] create a history include the notifications once that have bean rejected as well,
  - [] add current bounty to detail page and add bounty page
  - [] customize the django allauth page templates and email templates
     - email confirmation email
     - password reset email
     - password change email
     - email change email
     - signup and customize all the django allauth pages we come in contact with



### ----------- PROJECT MVP -------------
############################ TO DO LIST ############################
### ----- user should be abel to ------

- create an account
- suggest tow people which they know to be visible in the shadchins list of potential mates
- add a bounty to the suggestion that they suggest (to increase the likely hood the shadchan will take it seriously)
- submit there child (in theory any one with the info it takes to fill in the form can submit) with a bounty
- view a list of shadchonim and have the option to message them
- schedule a appointment
- call the shadchon
- add bounty to a person of interest ( to find a person user will need the persons name and address )

#### ----- user should be able to have full crud on all endpoints ------

- edit profile
- edit suggestion
- edit single person listing
- edit a message which was sent to shadchen ( all be it there will be a edited icon on the message )
- edit appointment

### ----- should should be able to ------

- view a list of all suggested matches in a extremely insightful way (more on that below ↓)
- view a list of all posted people as a individual in a extremely insightful way (more on that below ↓)
- call a person witch ether called or messaged them in the past
- add a suggestion from ether lists to there cart of in progress shiduchim ( which will enable them to claim all bounty's related to a individual after the office can verify the people in question are indeed married)
- file a bug fix
- flag troll's
- submit a success report to claim bounty

#### -------- some (list) filtering ideas. a point system will determine list placement ---------

- a shadchin will only see people from there community #chabad #syrian #litfish
- bounty should be displayed
- the amount of data the individual has on them will be displayed in a 1/10 ranking system
- data posted / updated ( the user can only change the updated date if the info ranking goes up )

#### ------------- list of perspective technology's --------------------

- messaging (look deeply into Django Channels)
- appointment's (look into calendly.com)

#### ------- data base models ---------

#### User

- first name
- last name
- age
- is_shadchen
- is_admin
- created at
- updated at
  -- user profile model
- address
- zip_code
- city
- country

#### Suggestion

------- Minimum whom is the suggestion--------
- account_holder_title / self, father, mother
- boy first name
- boy last name
- girls names
- parents names
- full address
- hight
- hear color
- profile upload optional
- brief description on y you think it is a good idea
  ------ Medium ---------
- current occupation
- shlichas
- aspirations
- introvert 1 to 5
- tziniyus----
- skurt over knee 1 to 5
- tight clothes or loses clothes 1 to 5 choices on the front end will be something like, baggie slimFit, fitted,






  view trello board https://trello.com/b/XJQQjt2t/plateias