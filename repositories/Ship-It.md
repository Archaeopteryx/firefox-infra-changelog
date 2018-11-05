## SHIP-IT MARKDOWN TABLE

| Commit Number | Commiter | Commit Message | Date | 
|:---:|:----:|:----------------------------------:|:----:| 
|0|Patrick Cloke|Bump Thunderbird to version 65. (#239)|2018-10-29T22:40:41Z
|1|Rob Lemley|Bug 1502445 - Remove obsolete locales from Thunderbird. (#241)  The downloads page on thunderbird.net uses thunderbird_primary_builds.json  to generate the download list. There's some locales included there  that have been removed from Thunderbird in bug 1310221. This patch  brings thunderbirddetails.py (mostly) inline with all-locales in  comm/mail/locales.|2018-10-29T22:30:04Z
|2|Rail Aliiev|Use raw string for regexes (#242)|2018-10-29T22:22:50Z
|3|Pascal Chevrel|Nightly 65: Merge and deply when 65 builds are available for all locales (#238)|2018-10-23T09:27:10Z
|4|Nick Thomas|Use N most recent releases only (#237)|2018-10-17T20:10:15Z
|5|Pascal Chevrel|Update false Fennec instructions in template (#236)|2018-09-10T16:20:59Z
|6|Patrick Cloke|Bump Thunderbird nightly version to 64. (#234)|2018-09-05T14:40:36Z
|7|Pascal Chevrel|Update available firefox nightly version to 64. (#233)|2018-09-05T14:28:27Z
|8|Julien Cristau|Bug 1460752 - bump CURRENT_ESR to 60 (#235)|2018-09-05T13:27:57Z
|9|Rail Aliiev|Reformat, add more info (#232)|2018-07-13T20:49:08Z
|10|Rail Aliiev|Handle "legacy" releases properly, kill python2.6 (#231)    Add "legacy" release      Break the tests      Do not return flask.Response object for legacy        When a release uses l10nChangesets: "legacy" (not available?), the      corresponding function (_getReleaseLocales) returns a flask.Response      object (generated by jsonify_by_sorting_values). This breaks the logic      when we export aggregated (combined betas) release JSON files, because      flask.Response is not JSON serializable.|2018-07-11T02:19:18Z
|11|Rail Aliiev|Deployment info (#230)|2018-07-10T15:44:51Z
|12|Rail Aliiev|Add deployment section (#229)|2018-07-10T14:06:41Z
|13|Rail Aliiev|Set iOS versions (#228)|2018-06-27T09:47:07Z
|14|Pascal Chevrel|Nightly 63: Merge when 63 builds are available for all locales (#225)|2018-06-26T14:05:31Z
|15|Patrick Cloke|Bump Thunderbird nightly version to 63. (#226)|2018-06-26T13:59:55Z
|16|Nick Thomas|Reland bug 1462120 - Firefox 60.0esr should be in firefox.json (#224)|2018-05-30T09:56:19Z
|17|Nick Thomas|Revert "Bug 1462120 - Firefox 60.0esr should be in firefox.json to create update verify configs (#222)" for busting Firefox beta releases (#223)  This reverts commit 90794c58730ec20d00a184399f12b04cadc45484.|2018-05-24T21:08:22Z
|18|Nick Thomas|Bug 1462120 - Firefox 60.0esr should be in firefox.json to create update verify configs (#222)|2018-05-23T23:35:01Z
|19|Julien Cristau|Set ESR_NEXT to 60 (#221)|2018-05-09T13:51:55Z
|20|Patrick Cloke|Bump Thunderbird nightly version to 62. (#220)|2018-05-08T02:20:00Z
|21|Pascal Chevrel|Nightly 62: Merge when 62 builds are available for all locales (#219)|2018-05-08T02:16:51Z
|22|Francesco Lodolo|Update l10n data for all locales (#218)|2018-05-02T14:05:47Z
|23|Francesco Lodolo|Bug 1458520 - Add 'en-CA' to product-details (#217)|2018-05-02T13:58:03Z
|24|Francesco Lodolo|Bug 1455045 - Add 'crh' to product-details (#216)  Also update language/region names for other locales|2018-04-18T18:43:51Z
|25|Patrick Cloke|Bump Thunderbird nightly version to 61. (#215)|2018-03-12T20:33:04Z
|26|Pascal Chevrel|Start Nightly 61 cycle (#214)|2018-03-12T19:51:27Z
|27|Ben Hearsum|Add devedition.json, and build_number to product exports (#213)|2018-02-09T13:54:16Z
|28|Patrick Cloke|Bump TB version to 60. (#212)|2018-02-05T14:55:48Z
|29|Pascal Chevrel|Nightly 60: Merge when 60 builds are available for all locales (#211)|2018-01-23T07:45:25Z

