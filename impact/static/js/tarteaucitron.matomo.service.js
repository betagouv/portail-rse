// matomocloud
tarteaucitron.services.matomocloudbeta = {
    "key": "matomocloudbeta",
    "type": "analytic",
    "name": "Matomo (privacy by design)",
    "uri": "https://matomo.org/faq/general/faq_146/",
    "needConsent": true,
    "cookies": ['_pk_ref', '_pk_cvar', '_pk_id', '_pk_ses', '_pk_hsr', 'mtm_consent', 'matomo_ignore', 'matomo_sessid'],
    "js": function () {
        "use strict";
        if (tarteaucitron.user.matomoId === undefined) {
            return;
        }

        window._paq = window._paq || [];
        window._paq.push(["requireConsent"]);
        window._paq.push(["setConsentGiven"]);
        window._paq.push(["setSiteId", tarteaucitron.user.matomoId]);
        window._paq.push(["setTrackerUrl", tarteaucitron.user.matomoHost + "matomo.php"]);
        window._paq.push(["enableLinkTracking"]);
        window._paq.push(["setExcludedQueryParams", ["simulationId", "_csrf"]]);
	window._paq.push(['HeatmapSessionRecording::enable']);

        if (tarteaucitron.user.matomoDontTrackPageView !== true) {
            window._paq.push(["trackPageView"]);
        }

        if (tarteaucitron.user.matomoFullTracking === true) {
            window._paq.push(["trackAllContentImpressions"]);
        }

        if (tarteaucitron.user.matomoCustomJSPath === undefined || tarteaucitron.user.matomoCustomJSPath == '') {
            tarteaucitron.addScript(tarteaucitron.user.matomoHost + 'matomo.js', '', '', true, 'defer', true);
        } else {
            tarteaucitron.addScript(tarteaucitron.user.matomoCustomJSPath, '', '', true, 'defer', true);
        }

        // waiting for Matomo to be ready to check first party cookies
        var interval = setInterval(function () {
            if (typeof Matomo === 'undefined') return

            clearInterval(interval)

            // make Matomo cookie accessible by getting tracker
            Matomo.getTracker();

            // looping through cookies
            var theCookies = document.cookie.split(';');
            for (var i = 1; i <= theCookies.length; i++) {
                var cookie = theCookies[i - 1].split('=');
                var cookieName = cookie[0].trim();

                // if cookie starts like a matomo one, register it
                if (cookieName.indexOf('_pk_') === 0) {
                    tarteaucitron.services.matomo.cookies.push(cookieName);
                }
            }
        }, 100);
    },
    "fallback": function () {
        "use strict";
        if (tarteaucitron.user.matomoId === undefined) {
            return;
        }

        window._paq = window._paq || [];
        window._paq.push(["requireConsent"]);
        window._paq.push(["setSiteId", tarteaucitron.user.matomoId]);
        window._paq.push(["setTrackerUrl", tarteaucitron.user.matomoHost + "matomo.php"]);
        window._paq.push(["trackPageView"]);
        window._paq.push(["enableLinkTracking"]);
        window._paq.push(["setExcludedQueryParams", ["simulationId", "_csrf"]]);

        if (tarteaucitron.user.matomoCustomJSPath === undefined || tarteaucitron.user.matomoCustomJSPath == '') {
            tarteaucitron.addScript(tarteaucitron.user.matomoHost + 'matomo.js', '', '', true, 'defer', true);
        } else {
            tarteaucitron.addScript(tarteaucitron.user.matomoCustomJSPath, '', '', true, 'defer', true);
        }
    }
};
