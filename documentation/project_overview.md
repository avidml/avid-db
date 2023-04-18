# AI Vulnerability Database
The [AI Vulnerability Database (AVID)](https://avidml.org) is an open-source knowledge base of failure modes for Artificial Intelligence (AI) models, datasets, and systems.

**Our Mission**

Empower communities to recognize, diagnose, and manage vulnerabilities in AI that affect them.

**Our Vision**

Our vision is to work across disciplines to make AI safer for everyone by exposing vulnerabilities in the AI ecosystem. We build tools for practitioners and communities to interrogate the growing number of models capable of producing material harm to our world. Together we operationalize AI risk management to protect the future of our world.

**Our Values**
* **Builders First** - Our community leads by example. We prioritize making things work over telling others how they should work. We come up with imperfect solutions to collectively iterate and improve upon.
* **Rigorous** - To make the impact we strive for we must hold ourselves to a high standard. While we may work in a scrappy fashion we build things with practical usage and interoperability in mind.
* **Vigilant** - We keep watch for new vulnerabilities and work together to cut through the hype around new AI products and innovations.
* **Courageous** - Our work demands we take action and speak against the growing reliance and proliferation of AI by corporations who put profit before all.
* **Respectful** - In all situations we treat each other with dignity. Different cultures, experiences, and circumstances create both conflict and the opportunity to come together. Only by appreciating those who are different from us can we find better ways forward.
* **Connective** - We reach out to those who hold different values, and have different needs, to find mutually beneficial solutions. Our effort to bridge gaps and break down barriers leads us to build tools and conduct research inclusive of individuals from all walks of life.
## Overview of the project
We are building the [database](https://avidml.org/database/) to be both an extension of, and a bridge between, the classic security-related vulnerabilities of the [National Vulnerability Database (NVD)](https://nvd.nist.gov/vuln), the explicitly adversarial vulnerabilities housed in the [MITRE ATLAS](https://atlas.mitre.org/), and the public incidents recorded in the [AI Incident Database (AIID)](https://incidentdatabase.ai/) to provide a comprehensive view into the AI Risk landscape. By bringing these disparate sources together, and adding in the unintentional failure states present throughout the AI ecosystem, we provide information to help guide people to build better. 

Developers can see the risks in particular models and datasets they want to build on top of, which will help them make better choices with less risk of harm. Communities will have a way to contest systems, models, and datasets that can cause harm to them, which gives them a voice in a conversation they are too often excluded from. Regulators, policy makers, and adjudicating bodies will benefit from having a clear picture of the landscape and which entities represent the greatest sources of harm.

Our [taxonomy](https://avidml.org/taxonomy/) is iteratively developed through consistent conversation with researchers, auditors, and communities to ensure it is useful today and provides actionable insights.

## Technical implementation
To foster trust we're building a secure and transparent system leveraging well-known infrastructure and methods. Our editorial process for reports, including contestation, will occur directly within github so that every decision is made within public view. We're building our database as a serverless application using core AWS services to provide scale and security while trying to minimize our carbon footprint. 

![System Diagram](/assets/system-diagram.jpg)*As you can see from the system diagram we have all of our open source code housed within github. Our Backend is run through AWS with direct usage of Github authentication, auditing, and an API that will allow people to integrate the data into their systems.*

We are building our systems so that anyone can adopt our [data model](https://github.com/avidml/avidtools/tree/main/avidtools/datamodels) to build their own database internal to their organization. By doing this we encourage a network of federated databases where AVID acts as the bridge both to the public and between private entities. We want people to perform ethical disclosure through AVID's editorial process while enabling them to leverage the standards we're building to improve their own internal product development.
## Editorial process
Today our editorial process starts with either a submission to our form, using airtable, or by someone creating an issue in Github. Then we have a manual four step process:
1. An editor maps inputs mapped to a Report datamodel and, published as json to `avid-db/reports/review`
2. The Editor manually checks and edits report as needed, moves it to `avid-db/reports/202X/AVID-202X-R000X.json`
3. The Editor manually converts report to vuln, saves it in `avid-db/vulnerabilities/202X/AVID-202X-V00X.json`
4. Webmaster renders new reports and vulns to .md files in `website/exampleSite/content/database`

We aim to make this less manual over the course of the next 6 months by building an editorial UI and creating the tools necessary to leverage our data model directly within other systems to make pushing reports to AVID easier and with more complete information up front. Our decisions for each report will be logged in Github so that it's done in an open and transparent manner.

![Editorial Process](/assets/editorial-process.jpg)*Here you can see that our goal is to support people submitting reports to AVID from any number of public model hubs and private repositories within their organization.*

## HuggingFace Space for educational purposes
To help make our database approachable, and as a proof of concept for people who may want to build direct integrations with AVID, we built a simple experience that highlights how detections work. We combined public datasets used for bias detection with statistical tests to show one meaningful way of identifying vulnerabilities within a model on HuggingFace. 

[![A Space on HuggingFace for detecting Bias with one click](/assets/plug-and-play-bias-detection-space.png)](https://huggingface.co/spaces/avid-ml/bias-detection)*Click the image to go to the space.*

The space allows a person to pick any model on the hub and test it across 3 datasets: [BOLD](https://github.com/amazon-science/bold), [HONEST](https://github.com/MilaNLProc/honest), and [WinoBias](https://uclanlp.github.io/corefBias/overview). It also allows for people to generate a report in the AVID Schema so that they could copy and paste it into a GitHub issue to submit a new report. Our hope is that people can use this tool to start thinking about how they can discover vulnerabilities and to get people familiar with our schema so that it is easier to adopt.

## Ways to contribute
Currently there are three ways to contribute to the project:
1. Join the community - We're currently on [Discord](https://discord.com/invite/FcXYZzmv3T). Once in you can bring your ideas, suggestions, comments, and skils to bear on making this serve our communities.
2. Partner with us - you can [email](mailto:arva@avidml.org) us to inquire about  research collaborations, co-development, or sponsorships.
3. Help us get funding - you can donate directly (we're in the process of getting our 501c3 status) or help us find grants we are eligible for.

This is a significant undertaking, at a critical time, and so we appreciate every bit of support we can muster. Thank you for taking the time to read this.