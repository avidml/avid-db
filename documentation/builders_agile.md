# ARVA Agile Practices Cheatsheet and Onboarding
This document outlines some of the terminology and methods our organization has adopted from Agile. It is not a comprehensive resource for learning Agile, and if you take the time to read this you will be equipped to build with us.

**Current as of:** `5/20/23`

**Point of Contact:** `Nathan Butters`

## What is Agile Software Development?
At it's core Agile Development is a mentality that prioritizes the way people work together and get things done over any type of process or artifcats. It focuses on delivering something that works at speed to give people something to react to. This makes it very flexible, which is good, and also highly variable, which can be painful. Through the manifesto and 12 principles many different ideologies have developed, each with their strengths and weaknesses. 

This page won't touch anything but the one we've chosen to move forward with: **Scrum**. 

### What is Scrum?
**Definition**
> Scrum is a process framework used to manage product development and other knowledge work. Scrum is empirical in that it provides a means for teams to establish a hypothesis of how they think something works, try it out, reflect on the experience, and make the appropriate adjustments. Source: [Scrum](https://www.agilealliance.org/glossary/scrum/).

**Events**
* Sprint
* Sprint Planning
* ~~Scrum meeting~~ Office Hours
* Sprint Review
* Sprint Retrospective

**Process**
> The Scrum Lifecycle consists of a series of Sprints, where the end result is a potentially shippable product increment. Inside of these sprints, all of the activities necessary for the development of the product occur on a small subset of the overall product.  Below is a description of the key steps in the Scrum Lifecycle:
> 1. Establish the Product Backlog.
> 2. The product owner and development team conduct Sprint Planning. Determine the scope of the Sprint in the first part of Sprint Planning and the plan for delivering that scope in the second half of Sprint Planning.
> 3. As the Sprint progresses, the development team performs the work necessary to deliver the selected product backlog items.
> 4. ~~On a daily basis, the development team coordinates their work in a Daily Scrum.~~
> 5. At the end of the Sprint, the development team delivers the Product Backlog Items selected during Sprint Planning. The development team holds a Sprint Review to show the customer the increment and get feedback. The development team and product owner also reflect on how the Sprint has proceeded so far and adapting their processes accordingly during a retrospective.
> 6. The Team repeats steps 2–5 until the desired outcome of the product have been met.
> 
> Source: [Scrum](https://www.agilealliance.org/glossary/scrum/).

We will not hold daily scrum meetings. We are making the product owner and scrum lead available throughout the sprint to help remove roadblocks. The team will be responsible for finding time to communicate synchronously or asynchronously. We will put in a weekly check-in to help expose any major blockers that do not get brought up throughout the week.

### How does ARVA use Scrum?
The main elements we've adopted, for now, are:
* `Time Boxed Sprints`
* `Sprint Planning`
* `Retrospectives` - an accountability mechanism for us to reflect on our progress and come up with a way to do things better
* `Velocity & Estimation` - to help us understand how we're progressing and think through how much capacity we need to meet our goals we're using relative estimation (see detailed explanation below)
* `Scrum Lead` - Facilitates the work by keeping people accountable to the process we've agreed to.
* `Product Owner` - Facilitates the work by helping people define the next best thing to work on.

### Resources and Further Reading
* [Agile Manifesto](https://agilemanifesto.org/) - the historic site containing the manifesto and 12 principles
  * [Cleaner Manifesto](https://www.agilealliance.org/agile101/the-agile-manifesto/)
  * [Cleaner 12 Principles](https://www.agilealliance.org/agile101/12-principles-behind-the-agile-manifesto/)
* [Agile 101](https://www.agilealliance.org/agile101/) - a fairly lucid description of Agile Software Development
* [Agile Product Ownership](https://www.youtube.com/watch?v=502ILHjX9EE) - A video explaining the scrum process from the stand point of the product owner
* Terms
  * [Scrum](https://www.agilealliance.org/glossary/scrum/)
  * [Velocity](https://www.agilealliance.org/glossary/velocity/)
  * [Estimation](https://www.agilealliance.org/glossary/estimation)

## Builders Working Group Process
Unlike organizations who run Scrum as their core way of managing developers, we're using elements of scrum to help foster better communication with our volunteers and collaborators. We're also using it to ensure people are able to hold themselves accountable and only take on the work they think they can accomplish within a given timeframe. 

### Tools
We will be using Github Projects to manage our work for now. It's simple enough and it directly integrates into our github repos. Alongside this, we'll be using Slack to facilitate asynchronous communication.

### Sprints
We will be using `2 week iterations` to start. This will help us try to move quickly and not overestimate what we can accomplish. Of the 14 days in a sprint the assumption is that each person will only work **AT MOST** on 10 days, we will target 6 to develop a baseline. This is for estimation purposes (see below).

Within the first week the team will find a time to meet to set out the goal for the sprint. This will be a clear, though abstracted, understanding of what the team will accomplish in the sprint. 

Any specific delvierables that MUST be finished by the end of the time will also be discussed at this point. Open questions will also be brought up here with the Product Owner and Scrum Lead being responsible to chase down answers.

Near the end of the sprint we will have a retrospective to discuss how we feel the sprint went and what we think should be improved. This will also serve as a review of the sprint, though the focus is on how we can make our future work better than our past work.

### Roles

**Product Owner** - This person will prioritize the long and medium term vision for AVID. They will help facilitate the building of the system diagram, and will answer questions about the `what`, `why`, and `why now` for work being done by the team.

**Scrum Lead** - This person will make sure the work gets done within the confines of the processes we've put in place. They will help unblock any immediate issues with development, if possible, or will highlight where we simply lack the experience or capacity to deliver on something we intended to get done within the sprint.

**Team** - These are all the people contributing to development. They will be responsible for thier own workloads, as we do not have a formal management structure. It is critical that every person feels comfortable reaching out for help and expressing concern about delivery early so we can pivot, swarm, or defer the work.

### Estimation, Status, Priority and Product Rank
This last section is the most critical for everyone to bookmark because these are the values we'll be using to make everything above work. They can be adjusted through our retrospectives if they don't work, and for now we're going to use the following as our source of thruth. 

**Estimation** - The `Estimate` field in Github will be filled out by the person assigned to the work. The number will represent how many days the person thinks it will take for them to work on it. This is **NOT** an account of accurate time estimation (where 1 day == 8 hours), rather this is an estimation of how much of the projected 10 days will be consumed by the task. We're hoping to complete 6 points per person to develop a baseline.

NOTE: If you have more or less availability in any given sprint then you can take on more or less work as meets your availability. The goal is to complete all assignments, not to meet a specific number.

NOTE: If several tasks are less than 1 day, then tasks should be added together into a single ticket with an estimate of 1.

**Status** - We will use the status field in Github to help organize work. Every ticket should have a status, even if it's just a draft.

* **`New`** - means you are writing it and don't know where it goes. 
* **`Product Backlog`** - Put ideas for features and tickets you don't know how to prioritize into here. The Product Owner will prioritize everything in here and then move it to the backlog.
* **`Backlog`** - This is where the bulk of work should be at the beginning of a sprint. People will grab work items from here.
* **`Ready`** - When you know what work you need to do to complete a ticket, or at least start hacking at it, and you have estimated the work then it should be marked as ready.
* **`In Progress`** - When you are working on a ticket it should be in progress. We won't tell you to not have more than one ticket in this phase at a time, but if you find you're too scattered then try to reduce how many things you're focusing on.
* **`In review`** - Once you think you have completed your work, put it in this phase and tag one or more people to be reviewers so that we can get another set of eyes on it. The goal will be to have all of our work in this phase or later by the last 3 days of the sprint.
* **`Done`** - Once work is completed and merged we can move it into the Done category. At which point it will be archived from the project to keep everything clean.

**Priority & Product Rank** - These two fields exist to help people understand what's the next most important thing to work on. They are both numeric fields and operate similarly though they are separated because one is used primarily within the Product Backlog while the other is used by the team in the backlog and the sprint.

* **`Product Rank`** - Helps guide what comes next as far as features. Strictly 1 number per ticket in ascending order, with no overlaps.
* **`Priority`** - Simple scale from 1-5. 
  * `1 == Highest Priority` - should absolutely get done this sprint, swarm if at risk
  * `2 == High Priority` - should get done this sprint, drop other work to get this done
  * `3 == Medium Priority` - default, get done this sprint
  * `4 == Low Priority` - stretch, get done if all other work is completed
  * `5 == Oops, why is this here?` - This shouldn't be in the sprint. Nothing should ever be classified as a 5. NOTE: we will use this if we need to mark something to get bumped from the sprint.
