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

Before contributing, please read our [Code of Conduct](CODE_OF_CONDUCT.md).
