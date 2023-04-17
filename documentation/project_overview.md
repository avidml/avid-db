# AI Vulnerability Data Base
The AI Vulnerability Database (AVID) is an open-source knowledge base of failure modes for Artificial Intelligence (AI) models, datasets, and systems.

## Overview of the project

## Technical implementation

## Editorial process

## HuggingFace Space for educational purposes
To help make our database approachable, and as a proof of concept for people who may want to build direct integrations with AVID, we built a simple experience that highlights how detections work. We combined public datasets used for bias detection with statistical tests to show one meaningful way of identifying vulnerabilities within a model on HuggingFace. 

<figure class="video_container">
<iframe
	src="https://avid-ml-bias-detection.hf.space"
	frameborder="0"
	width="850"
	height="450"
></iframe>
</figure>

The space allows a person to pick any model on the hub and test it across 3 datasets: [BOLD](https://github.com/amazon-science/bold), [HONEST](https://github.com/MilaNLProc/honest), and [WinoBias](https://uclanlp.github.io/corefBias/overview). It also allows for people to generate a report in the AVID Schema so that they could copy and paste it into a GitHub issue to submit a new report. Our hope is that people can use this tool to start thinking about how they can discover vulnerabilities and to get people familiar with our schema so that it is easier to adopt.

## Ways to contribute