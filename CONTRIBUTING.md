# Contributing

Contributions to this project are very welcome in whatever form these may be. We highly
appreciate bug reports, pull requests, and documentation improvements.

Any interaction with this project should adhere to our Code of Conduct, which you can
find below.

It should be noted that this project heavily relies on
[pdfminer.six](https://github.com/pdfminer/pdfminer.six) and many issues about loading
PDFs may be due to this package. We ask that you try to avoid filing bugs that are
likely to be being cases by pdfminer.six against this repository, but rather you should
report these bugs directly at
[pdfminer.six/issues](https://github.com/pdfminer/pdfminer.six/issues).

## Issues

Issues are very valuable to this project.

* Ideas are a valuable source of contributions others can make.
* Problems show where this project is lacking.
* With a question you show where contributors can improve the user experience.

Thank you for creating them. If you are submitting an issue and would be interested in
helping to work on the fix, please indicate this in the issue.

## Pull Requests

Pull requests are also very valuable. Before submitting a pull request, it is probably
a good idea to first submit an issue to discuss the matter. This helps to avoid wasting
your time working on something that may not be accepted.

When submitting a Pull Request, you will need to do the following things. There is a
checklist in the template to help make sure you don't forget.

We run type checks using both pytpe and mypy. We also enforce code style using
pycodestyle and black. You can run  `docker-compose run --rm lint` to check this.

* Provide a good description of the change, and the reason for it.
* Ensure the tests, type checks, and linting passes (this is done by continuous
  integration).
* Add any additional tests, as required.
* Ensure all of your changes are well documented.
* Update the CHANGELOG.md with a description of your changes, following the format from
  [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at jstockwin@gmail.com. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/
