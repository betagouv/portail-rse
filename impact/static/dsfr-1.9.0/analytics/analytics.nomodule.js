/*! DSFR v1.9.0 | SPDX-License-Identifier: MIT | License-Filename: LICENSE.md | restricted use (see terms and conditions) */

(function () {
  'use strict';

  var config = {
    prefix: 'fr',
    namespace: 'dsfr',
    organisation: '@gouvfr',
    version: '1.9.0'
  };

  var api = window[config.namespace];

  var patch = {
    namespace: 'a4e35ba2a938ba9d007689dbf3f46acbb9807869'
  };

  var Mode = {
    MANUAL: 'manual',
    AUTO: 'auto',
    NO_COMPONENTS: 'no_components'
  };

  var PUSH = 'EA_push';

  var Init = function Init (domain) {
    var this$1$1 = this;

    this._domain = domain;
    this._isLoaded = false;
    this._promise = new Promise(function (resolve, reject) {
      this$1$1._resolve = resolve;
      this$1$1._reject = reject;
    });
  };

  var prototypeAccessors$b = { id: { configurable: true },store: { configurable: true } };

  Init.prototype.configure = function configure () {
    this.pushing();
    this.load();
    return this._promise;
  };

  prototypeAccessors$b.id.get = function () {
    if (!this._id) {
      var bit = 5381;
      for (var i = this._domain.length - 1; i > 0; i--) { bit = (bit * 33) ^ this._domain.charCodeAt(i); }
      bit >>>= 0;
      this._id = "_EA_" + bit;
    }
    return this._id;
  };

  prototypeAccessors$b.store.get = function () {
    if (!this._store) {
      this._store = [];
      this._store.eah = this._domain;
      window[this.id] = this._store;
    }
    return this._store;
  };

  Init.prototype.pushing = function pushing () {
      var this$1$1 = this;

    if (!window[PUSH]) { window[PUSH] = function () {
        var args = [], len = arguments.length;
        while ( len-- ) args[ len ] = arguments[ len ];

        return this$1$1.store.push(args);
        }; }
  };

  Init.prototype.load = function load () {
    var stamp = new Date() / 1E7 | 0;
    var offset = stamp % 26;
    var key = String.fromCharCode(97 + offset, 122 - offset, 65 + offset) + (stamp % 1E3);
    this._script = document.createElement('script');
    this._script.ea = this.id;
    this._script.async = true;
    this._script.addEventListener('load', this.loaded.bind(this));
    this._script.addEventListener('error', this.error.bind(this));
    this._script.src = "//" + (this._domain) + "/" + key + ".js?2";
    var node = document.getElementsByTagName('script')[0];
    node.parentNode.insertBefore(this._script, node);
  };

  Init.prototype.error = function error () {
    api.inspector.error('unable to load Eulerian script file. the domain declared in your configuration must match the domain provided by the Eulerian interface (tag creation)');
    this._reject();
  };

  Init.prototype.loaded = function loaded () {
    if (this._isLoaded) { return; }
    this._isLoaded = true;
    this._resolve();
  };

  Object.defineProperties( Init.prototype, prototypeAccessors$b );

  /*  '["\'<>*$&~`|\\\\?^~]'; */
  var RESTRICTED = {
    '0x0022': '＂',
    '0x0024': '＄',
    '0x0026': '＆',
    '0x0027': '＇',
    '0x002a': '＊',
    '0x003c': '＜',
    '0x003e': '＞',
    '0x003f': '？',
    '0x005c': '＼',
    '0x005e': '＾',
    '0x0060': '｀',
    '0x007c': '｜',
    '0x007e': '～'
  };

  // import TABLE from './unicode-table';

  var charCodeHex = function (char) {
    var code = char.charCodeAt(0).toString(16);
    return '0x0000'.slice(0, -code.length) + code;
  };

  var normalize = function (text) {
    if (!text) { return text; }
    // text = [...text].map(char => TABLE[charCodeHex(char)] || char).join('');
    text = [].concat( text ).map(function (char) { return RESTRICTED[charCodeHex(char)] || char; }).join('');
    text = text.replace(/\s/g, '_');
    text = text.toLowerCase();
    return text;
  };

  var validateString = function (value, name, allowNull) {
    if ( allowNull === void 0 ) allowNull = true;

    switch (true) {
      case typeof value === 'number':
        return ("" + value);

      case typeof value === 'string':
        return value;

      case value === undefined && allowNull:
      case value === null && allowNull:
        return '';
    }

    api.inspector.warn(("unexpected value '" + value + "' set at analytics." + name + ". Expecting a String"));
    return null;
  };

  var validateNumber = function (value, name, allowNull) {
    if ( allowNull === void 0 ) allowNull = true;

    switch (true) {
      case !isNaN(value):
        return value;

      case typeof value === 'string' && !isNaN(Number(value)):
        return Number(value);

      case value === undefined && allowNull:
      case value === null && allowNull:
        return -1;
    }

    api.inspector.warn(("unexpected value '" + value + "' set at analytics." + name + ". Expecting a Number"));
    return null;
  };

  var validateBoolean = function (value, name) {
    switch (true) {
      case typeof value === 'boolean':
        return value;

      case typeof value === 'string' && value.toLowerCase() === 'true':
      case value === '1':
      case value === 1:
        return true;

      case typeof value === 'string' && value.toLowerCase() === 'false':
      case value === '0':
      case value === 0:
        return false;

      case value === undefined:
      case value === null:
        return value;
    }

    api.inspector.warn(("unexpected value '" + value + "' set at analytics." + name + ". Expecting a Boolean"));
    return null;
  };

  var validateLang = function (value, name, allowNull) {
    if ( allowNull === void 0 ) allowNull = true;

    switch (true) {
      case typeof value === 'string' && /^[A-Za-z]{2}$|^[A-Za-z]{2}[-_]/.test(value):
        return value.split(/[-_]/)[0].toLowerCase();

      case value === undefined && allowNull:
      case value === null && allowNull:
        return '';
    }

    api.inspector.warn(("unexpected value '" + value + "' set at analytics." + name + ". Expecting language as a String following ISO 639-1 format"));
    return null;
  };

  var validateGeography = function (value, name, allowNull) {
    if ( allowNull === void 0 ) allowNull = true;

    switch (true) {
      case typeof value === 'string':
        if (!/^FR-[A-Z0-9]{2,3}$/.test(value)) { api.inspector.warn(("value '" + value + "' set at analytics." + name + " with wrong format. Geographic location should be a String following ISO 3166-2:FR format")); }
        return value;

      case value === undefined && allowNull:
      case value === null && allowNull:
        return '';
    }

    api.inspector.warn(("unexpected value '" + value + "' set at analytics." + name + ". Expecting geographic location as a String following ISO 3166-2:FR format"));
    return null;
  };

  var Page = function Page (config) {
    this._config = config || {};
  };

  var prototypeAccessors$a = { path: { configurable: true },referrer: { configurable: true },title: { configurable: true },name: { configurable: true },labels: { configurable: true },categories: { configurable: true },isError: { configurable: true },template: { configurable: true },segment: { configurable: true },group: { configurable: true },subtemplate: { configurable: true },theme: { configurable: true },subtheme: { configurable: true },related: { configurable: true },depth: { configurable: true },current: { configurable: true },total: { configurable: true },filters: { configurable: true },layer: { configurable: true } };

  Page.prototype.reset = function reset (clear) {
      if ( clear === void 0 ) clear = false;

    this.path = clear ? '' : this._config.path || document.location.pathname;
    this.referrer = clear ? '' : this._config.referrer;
    var title = this._config.title || document.title;
    this.title = clear ? '' : title;
    this.name = clear ? '' : this._config.name || title;
    this._labels = clear || !this._config.labels ? ['', '', '', '', ''] : this._config.labels;
    this._categories = clear || !this._config.categories ? ['', '', ''] : this._config.categories;
    this._labels.length = 5;
    this.isError = !clear && this._config.isError;
    this.template = clear ? '' : this._config.template;
    this.group = clear ? '' : this._config.group;
    this.segment = clear ? '' : this._config.segment;
    this.subtemplate = clear ? '' : this._config.subtemplate;
    this.theme = clear ? '' : this._config.theme;
    this.subtheme = clear ? '' : this._config.subtheme;
    this.related = clear ? '' : this._config.related;
    this.depth = clear || isNaN(this._config.depth) ? 0 : this._config.depth;
    this.current = clear || isNaN(this._config.current) ? -1 : this._config.current;
    this.total = clear || isNaN(this._config.total) ? -1 : this._config.total;
    this._filters = clear || !this._config.filters ? [] : this._config.filters;
  };

  prototypeAccessors$a.path.set = function (value) {
    var valid = validateString(value, 'page.path');
    if (valid !== null) { this._path = valid; }
  };

  prototypeAccessors$a.path.get = function () {
    return this._path;
  };

  prototypeAccessors$a.referrer.set = function (value) {
    var valid = validateString(value, 'page.referrer');
    if (valid !== null) { this._referrer = valid; }
  };

  prototypeAccessors$a.referrer.get = function () {
    return this._referrer;
  };

  prototypeAccessors$a.title.set = function (value) {
    var valid = validateString(value, 'page.title');
    if (valid !== null) { this._title = valid; }
  };

  prototypeAccessors$a.title.get = function () {
    return this._title;
  };

  prototypeAccessors$a.name.set = function (value) {
    var valid = validateString(value, 'page.name');
    if (valid !== null) { this._name = valid; }
  };

  prototypeAccessors$a.name.get = function () {
    return this._name;
  };

  prototypeAccessors$a.labels.get = function () {
    return this._labels;
  };

  prototypeAccessors$a.categories.get = function () {
    return this._categories;
  };

  prototypeAccessors$a.isError.set = function (value) {
    var valid = validateBoolean(value, 'page.isError');
    if (valid !== null) { this._isError = valid; }
  };

  prototypeAccessors$a.isError.get = function () {
    return this._isError;
  };

  prototypeAccessors$a.template.set = function (value) {
    var valid = validateString(value, 'page.template');
    if (valid !== null) { this._template = valid; }
  };

  prototypeAccessors$a.template.get = function () {
    return this._template;
  };

  prototypeAccessors$a.segment.set = function (value) {
    var valid = validateString(value, 'page.segment');
    if (valid !== null) { this._segment = valid; }
  };

  prototypeAccessors$a.segment.get = function () {
    return this._segment;
  };

  prototypeAccessors$a.group.set = function (value) {
    var valid = validateString(value, 'page.group');
    if (valid !== null) { this._group = valid; }
  };

  prototypeAccessors$a.group.get = function () {
    return this._group;
  };

  prototypeAccessors$a.subtemplate.set = function (value) {
    var valid = validateString(value, 'page.subtemplate');
    if (valid !== null) { this._subtemplate = valid; }
  };

  prototypeAccessors$a.subtemplate.get = function () {
    return this._subtemplate;
  };

  prototypeAccessors$a.theme.set = function (value) {
    var valid = validateString(value, 'page.theme');
    if (valid !== null) { this._theme = valid; }
  };

  prototypeAccessors$a.theme.get = function () {
    return this._theme;
  };

  prototypeAccessors$a.subtheme.set = function (value) {
    var valid = validateString(value, 'page.subtheme');
    if (valid !== null) { this._subtheme = valid; }
  };

  prototypeAccessors$a.subtheme.get = function () {
    return this._subtheme;
  };

  prototypeAccessors$a.related.set = function (value) {
    var valid = validateString(value, 'page.related');
    if (valid !== null) { this._related = valid; }
  };

  prototypeAccessors$a.related.get = function () {
    return this._related;
  };

  prototypeAccessors$a.depth.set = function (value) {
    var valid = validateNumber(value, 'page.depth');
    if (valid !== null) { this._depth = valid; }
  };

  prototypeAccessors$a.depth.get = function () {
    return this._depth;
  };

  prototypeAccessors$a.current.set = function (value) {
    var valid = validateNumber(value, 'page.current');
    if (valid !== null) { this._current = valid; }
  };

  prototypeAccessors$a.current.get = function () {
    return this._current;
  };

  prototypeAccessors$a.total.set = function (value) {
    var valid = validateNumber(value, 'page.total');
    if (valid !== null) { this._total = valid; }
  };

  prototypeAccessors$a.total.get = function () {
    return this._total;
  };

  prototypeAccessors$a.filters.get = function () {
    return this._filters;
  };

  prototypeAccessors$a.layer.get = function () {
    var layer = [];
    if (this._path) { layer.push('path', normalize(this._path)); }
    if (this._referrer) { layer.push('referrer', normalize(this._referrer)); }
    var title = normalize(this._title);
    if (title) { layer.push('page_title', title); }
    if (this._name || title) { layer.push('page_name', normalize(this._name) || title); }

    var labels = this._labels.slice(0, 5);
    labels.length = 5;
    if (labels.some(function (label) { return label; })) { layer.push('pagelabel', labels.map(function (label) { return typeof label === 'string' ? normalize(label) : ''; }).join(',')); }

    this._categories.forEach(function (category, index) {
      if (category) { layer.push(("page_category" + (index + 1)), category); }
    });

    if (this._isError) { layer.push('error', '1'); }

    var template = normalize(this._template) || 'autres';
    layer.push('page_template', template);
    layer.push('pagegroup', normalize(this._group) || template);
    layer.push('site-segment', normalize(this._segment) || template);

    if (this._subtemplate) { layer.push('page_subtemplate', normalize(this._subtemplate)); }
    if (this._theme) { layer.push('page_theme', normalize(this._theme)); }
    if (this._subtheme) { layer.push('page_subtheme', normalize(this._subtheme)); }
    if (this._related) { layer.push('page_related', normalize(this._related)); }
    if (!isNaN(this._depth)) { layer.push('page_depth', this._depth); }

    if (!isNaN(this._current) && this._current > -1) {
      var pagination = "" + (this._current);
      if (!isNaN(this._total) && this._total > -1) { pagination += "/" + (this._total); }
      layer.push('page_pagination', pagination);
    }

    if (this._filters.length && this._filters.some(function (label) { return label; })) {
      var filters = this._filters.map(function (filter) { return typeof filter === 'string' ? normalize(filter) : ''; });
      layer.push('page_filters', filters.join(','));
    }
    return layer;
  };

  Object.defineProperties( Page.prototype, prototypeAccessors$a );

  var Environment = {
    DEVELOPMENT: {
      id: 'development',
      value: 'dev'
    },
    STAGE: {
      id: 'stage',
      value: 'stage'
    },
    PRODUCTION: {
      id: 'production',
      value: 'prod'
    }
  };

  var Site = function Site (config) {
    this._config = config || {};
  };

  var prototypeAccessors$9 = { environment: { configurable: true },entity: { configurable: true },language: { configurable: true },target: { configurable: true },type: { configurable: true },region: { configurable: true },department: { configurable: true },layer: { configurable: true } };

  Site.prototype.reset = function reset (clear) {
      if ( clear === void 0 ) clear = false;

    this.environment = clear ? undefined : this._config.environment;
    this.entity = clear ? undefined : this._config.entity;
    this.language = clear ? document.documentElement.lang : this._config.language || document.documentElement.lang;
    this.target = clear ? undefined : this._config.target;
    this.type = clear ? undefined : this._config.type;
    this.region = clear ? undefined : this._config.region;
    this.department = clear ? undefined : this._config.department;
  };

  prototypeAccessors$9.environment.set = function (value) {
    switch (value) {
      case Environment.PRODUCTION.id:
      case Environment.PRODUCTION.value:
        this._environment = Environment.PRODUCTION;
        break;

      case Environment.STAGE.id:
      case Environment.STAGE.value:
        this._environment = Environment.STAGE;
        break;

      case Environment.DEVELOPMENT.id:
      case Environment.DEVELOPMENT.value:
        this._environment = Environment.DEVELOPMENT;
        break;

      default:

        this._environment = Environment.DEVELOPMENT;
    }
  };

  prototypeAccessors$9.environment.get = function () {
    return this._environment.id;
  };

  prototypeAccessors$9.entity.set = function (value) {
    var valid = validateString(value, 'site.entity');
    if (valid !== null) { this._entity = valid; }
  };

  prototypeAccessors$9.entity.get = function () {
    return this._entity;
  };

  prototypeAccessors$9.language.set = function (value) {
    var valid = validateLang(value, 'site.language');
    if (valid !== null) { this._language = valid; }
  };

  prototypeAccessors$9.language.get = function () {
    return this._language;
  };

  prototypeAccessors$9.target.set = function (value) {
    var valid = validateString(value, 'site.target');
    if (valid !== null) { this._target = valid; }
  };

  prototypeAccessors$9.target.get = function () {
    return this._target;
  };

  prototypeAccessors$9.type.set = function (value) {
    var valid = validateString(value, 'site.type');
    if (valid !== null) { this._type = valid; }
  };

  prototypeAccessors$9.type.get = function () {
    return this._type;
  };

  prototypeAccessors$9.region.set = function (value) {
    var valid = validateGeography(value, 'site.region');
    if (valid !== null) { this._region = valid; }
  };

  prototypeAccessors$9.region.get = function () {
    return this._region;
  };

  prototypeAccessors$9.department.set = function (value) {
    var valid = validateGeography(value, 'site.department');
    if (valid !== null) { this._department = valid; }
  };

  prototypeAccessors$9.department.get = function () {
    return this._department;
  };

  prototypeAccessors$9.layer.get = function () {
    var layer = [];
    layer.push('site_environment', this._environment.value);
    if (this._entity) { layer.push('site_entity', normalize(this._entity)); }
    else { api.inspector.warn('entity is required in analytics.site'); }
    if (this._language) { layer.push('site_language', this._language); }
    if (this._target) { layer.push('site_target', normalize(this._target)); }
    if (this._type) { layer.push('site_type', normalize(this._type)); }
    if (this._region) { layer.push('site_region', this._region); }
    if (this._department) { layer.push('site_department', this._department); }
    return layer;
  };

  Object.defineProperties( Site.prototype, prototypeAccessors$9 );

  Site.Environment = Environment;

  var Status = {
    CONNECTED: {
      id: 'connected',
      value: 'connecté',
      isConnected: true,
      isDefault: true
    },
    ANONYMOUS: {
      id: 'anonymous',
      value: 'anonyme',
      isConnected: false,
      isDefault: true
    },
    GUEST: {
      id: 'guest',
      value: 'invité',
      isConnected: false
    }
  };

  var Profile = {
    VISITOR: {
      id: 'visitor',
      value: 'visitor'
    },
    LOOKER: {
      id: 'looker',
      value: 'looker'
    },
    SHOPPER: {
      id: 'shopper',
      value: 'shopper'
    },
    BUYER: {
      id: 'buyer',
      value: 'buyer'
    },
    REBUYER: {
      id: 'rebuyer',
      value: 'rebuyer'
    }
  };

  var Type$2 = {
    INDIVIDUAL: {
      id: 'individual',
      value: 'part'
    },
    PROFESSIONNAL: {
      id: 'professionnal',
      value: 'pro'
    }
  };

  var User = function User (config) {
    this._config = config || {};
  };

  var prototypeAccessors$8 = { uid: { configurable: true },email: { configurable: true },isNew: { configurable: true },status: { configurable: true },profile: { configurable: true },language: { configurable: true },type: { configurable: true },layer: { configurable: true } };

  User.prototype.reset = function reset (clear) {
      if ( clear === void 0 ) clear = false;

    this._isConnected = false;
    this.status = Status.ANONYMOUS;
    if (!clear && this._config.connect) { this.connect(this._config.connect.uid, this._config.connect.email, this._config.connect.isNew); }
    else {
      this._uid = undefined;
      this._email = undefined;
      this._isNew = false;
    }
    this.profile = clear ? undefined : this._config.profile;
    this.language = clear ? navigator.language : this._config.language || navigator.language;
    this.type = clear ? undefined : this._config.type;
  };

  User.prototype.connect = function connect (uid, email, isNew) {
      if ( isNew === void 0 ) isNew = false;

    this._uid = validateString(uid, 'user.uid');
    if (/^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]{2,}@[a-zA-Z0-9-]{2,}\.[a-zA-Z]{2,}$/.test(email)) { api.inspector.warn('Please check analytics.user.email is properly encrypted '); }
    this._email = validateString(email, 'user.email');
    this._isNew = validateBoolean(isNew);
    this._isConnected = true;
    this.status = Status.CONNECTED;
  };

  prototypeAccessors$8.uid.get = function () {
    return this._uid;
  };

  prototypeAccessors$8.email.get = function () {
    return this._email;
  };

  prototypeAccessors$8.isNew.get = function () {
    return this._isNew;
  };

  prototypeAccessors$8.status.set = function (id) {
      var this$1$1 = this;

    var stati = Object.values(Status).filter(function (status) { return status.isConnected === this$1$1._isConnected; });
    this._status = stati.filter(function (status) { return status.id === id || status.value === id; })[0] || stati.filter(function (status) { return status.isDefault; })[0];
  };

  prototypeAccessors$8.status.get = function () {
    return this._status.id;
  };

  prototypeAccessors$8.profile.set = function (id) {
    this._profile = Object.values(Profile).filter(function (profile) { return profile.id === id || profile.value === id; })[0];
  };

  prototypeAccessors$8.profile.get = function () {
    return this._profile.id;
  };

  prototypeAccessors$8.language.set = function (value) {
    var valid = validateLang(value, 'user.language');
    if (valid !== null) { this._language = valid; }
  };

  prototypeAccessors$8.language.get = function () {
    return this._language;
  };

  prototypeAccessors$8.type.set = function (id) {
    this._type = Object.values(Type$2).filter(function (type) { return type.id === id || type.value === id; })[0];
  };

  prototypeAccessors$8.type.get = function () {
    return this._type.id;
  };

  prototypeAccessors$8.layer.get = function () {
    var layer = [];
    if (this._uid) { layer.push('uid', normalize(this._uid)); }
    if (this._email) { layer.push('email', normalize(this._email)); }
    if (this._isNew) { layer.push('newcustomer', '1'); }
    if (this._profile) { layer.push('profile', this._profile.value); }
    if (this._status) { layer.push('user_login_status', this._status.value); }
    if (this._language) { layer.push('user_language', this._language); }
    if (this._type) { layer.push('user_type', this._type.value); }
    return layer;
  };

  Object.defineProperties( User.prototype, prototypeAccessors$8 );

  User.Status = Status;
  User.Profile = Profile;
  User.Type = Type$2;

  var Method = {
    STANDARD: {
      id: 'standard',
      value: 'standard',
      isDefault: true
    },
    AUTOCOMPLETE: {
      id: 'autocomplete',
      value: 'autocompletion'
    }
  };

  var Search = function Search (config) {
    this._config = config || {};
  };

  var prototypeAccessors$7 = { engine: { configurable: true },results: { configurable: true },terms: { configurable: true },category: { configurable: true },theme: { configurable: true },type: { configurable: true },method: { configurable: true },layer: { configurable: true } };

  Search.prototype.reset = function reset (clear) {
      if ( clear === void 0 ) clear = false;

    this.engine = clear ? undefined : this._config.engine;
    this.results = clear || isNaN(this._config.results) ? -1 : this._config.results;
    this.terms = clear ? undefined : this._config.terms;
    this.category = clear ? undefined : this._config.category;
    this.theme = clear ? undefined : this._config.theme;
    this.type = clear ? undefined : this._config.type;
    this.method = clear ? undefined : this._config.method;
  };

  prototypeAccessors$7.engine.set = function (value) {
    var valid = validateString(value, 'search.engine');
    if (valid !== null) { this._engine = valid; }
  };

  prototypeAccessors$7.engine.get = function () {
    return this._engine;
  };

  prototypeAccessors$7.results.set = function (value) {
    var valid = validateNumber(value, 'search.results');
    if (valid !== null) { this._results = valid; }
  };

  prototypeAccessors$7.results.get = function () {
    return this._results;
  };

  prototypeAccessors$7.terms.set = function (value) {
    var valid = validateString(value, 'search.terms');
    if (valid !== null) { this._terms = valid; }
  };

  prototypeAccessors$7.terms.get = function () {
    return this._terms;
  };

  prototypeAccessors$7.category.set = function (value) {
    var valid = validateString(value, 'search.category');
    if (valid !== null) { this._category = valid; }
  };

  prototypeAccessors$7.category.get = function () {
    return this._category;
  };

  prototypeAccessors$7.theme.set = function (value) {
    var valid = validateString(value, 'search.theme');
    if (valid !== null) { this._theme = valid; }
  };

  prototypeAccessors$7.theme.get = function () {
    return this._theme;
  };

  prototypeAccessors$7.type.set = function (value) {
    var valid = validateString(value, 'search.type');
    if (valid !== null) { this._type = valid; }
    this._type = value;
  };

  prototypeAccessors$7.type.get = function () {
    return this._type;
  };

  prototypeAccessors$7.method.set = function (id) {
    var methods = Object.values(Method);
    this._method = methods.filter(function (method) { return method.id === id || method.value === id; })[0] || methods.filter(function (method) { return method.isDefault; })[0];
  };

  prototypeAccessors$7.method.get = function () {
    return this._method;
  };

  prototypeAccessors$7.layer.get = function () {
    var layer = [];
    if (this._engine) { layer.push('isearchengine', normalize(this._engine)); }
    if (this._results > -1) { layer.push('isearchresults', this._results); }
    if (this._terms) { layer.push('isearchkey', 'search_terms', 'isearchdata', normalize(this._terms)); }
    if (this._category) { layer.push('isearchkey', 'search_category', 'isearchdata', normalize(this._category)); }
    if (this._theme) { layer.push('isearchkey', 'search_theme', 'isearchdata', normalize(this._theme)); }
    if (this._type) { layer.push('isearchkey', 'search_type', 'isearchdata', normalize(this._type)); }
    if (this._method && layer.length) { layer.push('isearchkey', 'search_method', 'isearchdata', this._method.value); }
    return layer;
  };

  Object.defineProperties( Search.prototype, prototypeAccessors$7 );

  Search.Method = Method;

  var Funnel = function Funnel (config) {
    this._config = config || {};
  };

  var prototypeAccessors$6 = { id: { configurable: true },type: { configurable: true },name: { configurable: true },step: { configurable: true },current: { configurable: true },total: { configurable: true },objective: { configurable: true },error: { configurable: true },layer: { configurable: true } };

  Funnel.prototype.reset = function reset (clear) {
      if ( clear === void 0 ) clear = false;

    this.id = clear ? undefined : this._config.id;
    this.type = clear ? undefined : this._config.type;
    this.name = clear ? undefined : this._config.name;
    this.step = clear ? undefined : this._config.step;
    this.current = clear || isNaN(this._config.current) ? -1 : this._config.current;
    this.total = clear || isNaN(this._config.total) ? -1 : this._config.total;
    this.objective = clear ? undefined : this._config.objective;
    this.error = clear ? undefined : this._config.error;
  };

  prototypeAccessors$6.id.set = function (value) {
    var valid = validateString(value, 'funnel.id');
    if (valid !== null) { this._id = valid; }
  };

  prototypeAccessors$6.id.get = function () {
    return this._id;
  };

  prototypeAccessors$6.type.set = function (value) {
    var valid = validateString(value, 'funnel.type');
    if (valid !== null) { this._type = valid; }
  };

  prototypeAccessors$6.type.get = function () {
    return this._type;
  };

  prototypeAccessors$6.name.set = function (value) {
    var valid = validateString(value, 'funnel.name');
    if (valid !== null) { this._name = valid; }
  };

  prototypeAccessors$6.name.get = function () {
    return this._name;
  };

  prototypeAccessors$6.step.set = function (value) {
    var valid = validateString(value, 'funnel.step');
    if (valid !== null) { this._step = valid; }
  };

  prototypeAccessors$6.step.get = function () {
    return this._step;
  };

  prototypeAccessors$6.current.set = function (value) {
    var valid = validateNumber(value, 'funnel.current');
    if (valid !== null) { this._current = valid; }
  };

  prototypeAccessors$6.current.get = function () {
    return this._current;
  };

  prototypeAccessors$6.total.set = function (value) {
    var valid = validateNumber(value, 'funnel.total');
    if (valid !== null) { this._total = valid; }
  };

  prototypeAccessors$6.total.get = function () {
    return this._total;
  };

  prototypeAccessors$6.objective.set = function (value) {
    var valid = validateString(value, 'funnel.objective');
    if (valid !== null) { this._objective = valid; }
    this._objective = value;
  };

  prototypeAccessors$6.objective.get = function () {
    return this._objective;
  };

  prototypeAccessors$6.error.set = function (value) {
    var valid = validateString(value, 'funnel.error');
    if (valid !== null) { this._error = valid; }
    this._error = value;
  };

  prototypeAccessors$6.error.get = function () {
    return this._error;
  };

  prototypeAccessors$6.layer.get = function () {
    var layer = [];
    if (this._id) { layer.push('funnel_id', normalize(this._id)); }
    if (this._type) { layer.push('funnel_type', normalize(this._type)); }
    if (this._name) { layer.push('funnel_name', normalize(this._name)); }
    if (this._step) { layer.push('funnel_step_name', normalize(this._step)); }
    if (!isNaN(this._current) && this._current > -1) { layer.push('funnel_step_number', this._current); }
    if (!isNaN(this._total) && this._total > -1) { layer.push('funnel_step_max', this._total); }
    if (this._objective) { layer.push('funnel_objective', normalize(this._objective)); }
    if (this._error) { layer.push('funnel_error', normalize(this._error)); }
    return layer;
  };

  Object.defineProperties( Funnel.prototype, prototypeAccessors$6 );

  var State = {
    UNKNOWN: -1,
    CONFIGURING: 0,
    CONFIGURED: 1,
    INITIATED: 2,
    READY: 3
  };

  var TarteAuCitronIntegration = function TarteAuCitronIntegration (config) {
    var this$1$1 = this;

    this._config = config;
    this._state = State.UNKNOWN;
    this._promise = new Promise(function (resolve, reject) {
      this$1$1._resolve = resolve;
      this$1$1._reject = reject;
    });
  };

  TarteAuCitronIntegration.prototype.configure = function configure () {
    if (this._state >= State.CONFIGURED) { return this._promise; }
    if (this._state === State.UNKNOWN) {
      api.inspector.info('analytics configures tarteaucitron');
      this._state = State.CONFIGURING;
    }

    var tarteaucitron = window.tarteaucitron;
    if (!tarteaucitron || !tarteaucitron.services) {
      window.requestAnimationFrame(this.configure.bind(this));
      return;
    }

    this._state = State.CONFIGURED;
    var init = this.init.bind(this);

    var data = {
      key: 'eulerian',
      type: 'analytic',
      name: 'Eulerian Analytics',
      needConsent: true,
      cookies: ['etuix'],
      uri: 'https://eulerian.com/vie-privee',
      js: init,
      fallback: function () { tarteaucitron.services.eulerian.js(); }
    };

    tarteaucitron.services.eulerian = data;
    if (!tarteaucitron.job) { tarteaucitron.job = []; }
    tarteaucitron.job.push('eulerian');

    return this._promise;
  };

  TarteAuCitronIntegration.prototype.init = function init () {
    if (this._state >= State.INITIATED) { return; }
    this._state = State.INITIATED;
    window.__eaGenericCmpApi = this.integrate.bind(this);
    var update = this.update.bind(this);
    window.addEventListener('tac.close_alert', update);
    window.addEventListener('tac.close_panel', update);
  };

  TarteAuCitronIntegration.prototype.integrate = function integrate (cmpApi) {
    if (this._state >= State.READY) { return; }
    this._state = State.READY;
    this._cmpApi = cmpApi;

    api.inspector.info('analytics has integrated tarteaucitron');

    this._resolve();
    this.update();
  };

  TarteAuCitronIntegration.prototype.update = function update () {
    if (this._state < State.READY) { return; }
    this._cmpApi('tac', window.tarteaucitron, 1);
  };

  var ConsentManagerPlatform = function ConsentManagerPlatform (config) {
    this._config = config;

    if (config) {
      switch (config.id) {
        case 'tarteaucitron':
          this.integrateTarteAuCitron();
          break;
      }
    }
  };

  ConsentManagerPlatform.prototype.integrateTarteAuCitron = function integrateTarteAuCitron () {
    this._tac = new TarteAuCitronIntegration(this._config);
    return this._tac.configure();
  };

  var ActionMode = {
    IN: 'in',
    OUT: 'out',
    NONE: 'none'
  };

  var ActionStatus = {
    UNSTARTED: {
      id: 'unstarted',
      value: -1
    },
    STARTED: {
      id: 'started',
      value: 1
    },
    ENDED: {
      id: 'ended',
      value: 2
    }
  };

  var getParametersLayer = function (data) {
    return Object.entries(data).map(function (ref) {
      var key = ref[0];
      var value = ref[1];

      return ['actionpname', normalize(key), 'actionpvalue', normalize(value)];
    }).flat();
  };

  var Action = function Action (name, isCollectable) {
    if ( isCollectable === void 0 ) isCollectable = false;

    this._isMuted = false;
    this._name = name;
    this._isCollectable = isCollectable;
    this._status = ActionStatus.UNSTARTED;
    this._labels = [];
    this._parameters = {};
  };

  var prototypeAccessors$5 = { isMuted: { configurable: true },isCollectable: { configurable: true },status: { configurable: true },name: { configurable: true },labels: { configurable: true },reference: { configurable: true },parameters: { configurable: true },_base: { configurable: true } };

  prototypeAccessors$5.isMuted.get = function () {
    return this._isMuted;
  };

  prototypeAccessors$5.isMuted.set = function (value) {
    this._isMuted = value;
  };

  prototypeAccessors$5.isCollectable.get = function () {
    return this._isCollectable && this._status === ActionStatus.UNSTARTED;
  };

  prototypeAccessors$5.status.get = function () {
    return this._status;
  };

  prototypeAccessors$5.name.get = function () {
    return this._name;
  };

  prototypeAccessors$5.labels.get = function () {
    return this._labels;
  };

  prototypeAccessors$5.reference.get = function () {
    return this._reference;
  };

  prototypeAccessors$5.parameters.get = function () {
    return this._parameters;
  };

  Action.prototype.addParameter = function addParameter (key, value) {
    this._parameters[key] = value;
  };

  Action.prototype.removeParameter = function removeParameter (key) {
    delete this._parameters[key];
  };

  prototypeAccessors$5.reference.set = function (value) {
    var valid = validateString(value, ("action " + (this._name)));
    if (valid !== null) { this._reference = valid; }
  };

  prototypeAccessors$5._base.get = function () {
    return ['actionname', this._name];
  };

  Action.prototype._getLayer = function _getLayer (mode, data) {
      if ( data === void 0 ) data = {};

    if (this._isMuted) { return []; }
    var layer = this._base;
    switch (mode) {
      case ActionMode.IN:
      case ActionMode.OUT:
        layer.push('actionmode', mode);
        break;
    }

    var labels = this._labels.slice(0, 5);
    labels.length = 5;
    if (labels.some(function (label) { return label; })) { layer.push('actionlabel', labels.map(function (label) { return typeof label === 'string' ? normalize(label) : ''; }).join(',')); }

    if (this._reference) { layer.push('actionref', this._reference); }

    if (data) {
      var merge = Object.assign({}, this._parameters, data);
      layer.push.apply(layer, getParametersLayer(merge));
    }
    return layer;
  };

  Action.prototype.start = function start (data) {
    if (this._status.value > ActionStatus.UNSTARTED.value) {
      api.inspector.error(("unexpected start on action " + (this._name) + " with status " + (this._status.id)));
      return;
    }
    var layer = this._getLayer(ActionMode.IN, data);
    this._status = ActionStatus.STARTED;
    return layer;
  };

  Action.prototype.end = function end (data) {
    var layer = this._getLayer(this._status === ActionStatus.STARTED ? ActionMode.OUT : ActionMode.NONE, data);
    this._status = ActionStatus.ENDED;
    return layer;
  };

  Action.prototype.resume = function resume (data) {
    if (this._isMuted) { return []; }
    if (this._status.value >= ActionStatus.ENDED.value) {
      api.inspector.error(("unexpected resuming on action " + (this._name) + " with status " + (this._status.id)));
      return [];
    }
    var layer = this._base;
    if (data) { layer.push.apply(layer, getParametersLayer(data)); }
    return layer;
  };

  Object.defineProperties( Action.prototype, prototypeAccessors$5 );

  var Actions = function Actions () {
    this._actions = [];
  };

  var prototypeAccessors$4 = { layers: { configurable: true } };

  Actions.prototype.getAction = function getAction (name, isCollectable) {
      if ( isCollectable === void 0 ) isCollectable = false;

    var action = this._actions.filter(function (action) { return action.name === name; })[0];
    if (!action) {
      action = new Action(name, isCollectable);
      this._actions.push(action);
    }
    return action;
  };

  Actions.prototype.hasAction = function hasAction (name) {
    return this._actions.some(function (action) { return action.name === name; });
  };

  Actions.prototype.remove = function remove (action) {
    var index = this._actions.indexOf(action);
    if (index === -1) { return false; }
    this._actions.splice(index, 1);
    return true;
  };

  prototypeAccessors$4.layers.get = function () {
    return this._actions.filter(function (action) { return action.isCollectable; }).map(function (action) { return action.start(); });
  };

  Object.defineProperties( Actions.prototype, prototypeAccessors$4 );

  Actions.ActionMode = ActionMode;

  var actions = new Actions();
  Actions.instance = actions;

  var push = function (type, layer) {
    if (typeof window.EA_push !== 'function') {
      api.inspector.warn('Analytics datalayer not sent, Eulerian API isn\'t yet avalaible');
      return;
    }

    api.inspector.log('analytics', type, layer);

    window.EA_push(type, layer);
  };

  var PushType = {
    COLLECTOR: 'collector',
    ACTION: 'action',
    ACTION_PARAMETER: 'actionparam'
  };

  var SLICE = 50;

  var Analytics = function Analytics () {
    var this$1$1 = this;

    this._isReady = false;
    this._readiness = new Promise(function (resolve, reject) {
      if (this$1$1._isReady) { resolve(); }
      else {
        this$1$1._resolve = resolve;
        this$1$1._reject = reject;
      }
    });
    this._configure(api);
  };

  var prototypeAccessors$3 = { isReady: { configurable: true },readiness: { configurable: true },page: { configurable: true },user: { configurable: true },site: { configurable: true },search: { configurable: true },funnel: { configurable: true },cmp: { configurable: true } };

  Analytics.prototype._configure = function _configure (api) {
    switch (true) {
      case window[patch.namespace] !== undefined:
        this._config = window[patch.namespace].configuration.analytics;
        window[patch.namespace].promise.then(this._build.bind(this), function () {});
        break;

      case api.internals !== undefined && api.internals.configuration !== undefined && api.internals.configuration.analytics !== undefined && api.internals.configuration.analytics.domain !== undefined:
        this._config = api.internals.configuration.analytics;
        this._build();
        break;

      case api.analytics !== undefined && api.analytics.domain !== undefined:
        this._config = api.analytics;
        this._build();
        break;

      default:
        api.inspector.warn('analytics configuration is incorrect or missing (required : domain)');
    }
  };

  Analytics.prototype._build = function _build () {
    switch (this._config.mode) {
      case Mode.MANUAL:
        this._mode = Mode.MANUAL;
        break;

      case Mode.NO_COMPONENTS:
        this._mode = Mode.NO_COMPONENTS;
        break;

      case Mode.AUTO:
      default:
        this._mode = Mode.AUTO;
    }

    this._init = new Init(this._config.domain);

    this._user = new User(this._config.user);
    this._site = new Site(this._config.site);
    this._page = new Page(this._config.page);
    this._search = new Search(this._config.search);
    this._funnel = new Funnel(this._config.funnel);

    this.reset();

    this._init.configure().then(this._start.bind(this), this._reject);
  };

  prototypeAccessors$3.isReady.get = function () {
    return this._isReady;
  };

  prototypeAccessors$3.readiness.get = function () {
    return this._readiness;
  };

  Analytics.prototype._start = function _start () {
    if (this._isReady) { return; }
    this._isReady = true;
    this._resolve();

    this._cmp = new ConsentManagerPlatform(this._config.cmp);

    switch (this._mode) {
      case Mode.AUTO:
      case Mode.NO_COMPONENTS:
        this.collect();
        break;
    }
  };

  prototypeAccessors$3.page.get = function () {
    return this._page;
  };

  prototypeAccessors$3.user.get = function () {
    return this._user;
  };

  prototypeAccessors$3.site.get = function () {
    return this._site;
  };

  prototypeAccessors$3.search.get = function () {
    return this._search;
  };

  prototypeAccessors$3.funnel.get = function () {
    return this._funnel;
  };

  prototypeAccessors$3.cmp.get = function () {
    return this._cmp;
  };

  Analytics.prototype.push = function push$1 (type, layer) {
    push(type, layer);
  };

  Analytics.prototype.reset = function reset (clear) {
      if ( clear === void 0 ) clear = false;

    this._user.reset(clear);
    this._site.reset(clear);
    this._page.reset(clear);
    this._search.reset(clear);
    this._funnel.reset(clear);
  };

  Analytics.prototype.collect = function collect () {
    var actionLayers = actions.layers;

    var layer = ( this._user.layer ).concat( this._site.layer,
      this._page.layer,
      this._search.layer,
      this._funnel.layer
    );

    var length = ((actionLayers.length / SLICE) + 1) | 0;
    for (var i = 0; i < length; i++) {
      var slice = actionLayers.slice(i * SLICE, (i + 1) * SLICE);
      layer.push.apply(layer, slice.flat());
      this.push(PushType.COLLECTOR, layer);
      layer = [];
    }
  };

  Object.defineProperties( Analytics.prototype, prototypeAccessors$3 );

  var analytics = new Analytics();

  analytics.Mode = Mode;
  analytics.PushType = PushType;

  /**
   * Copy properties from multiple sources including accessors.
   * source : https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Global_Objects/Object/assign#copier_des_accesseurs
   *
   * @param {object} [target] - Target object to copy into
   * @param {...objects} [sources] - Multiple objects
   * @return {object} A new object
   *
   * @example
   *
   *     const obj1 = {
   *        key: 'value'
   *     };
   *     const obj2 = {
   *        get function01 () {
   *          return a-value;
   *        }
   *        set function01 () {
   *          return a-value;
   *        }
   *     };
   *     completeAssign(obj1, obj2)
   */
  var completeAssign = function (target) {
    var sources = [], len = arguments.length - 1;
    while ( len-- > 0 ) sources[ len ] = arguments[ len + 1 ];

    sources.forEach(function (source) {
      var descriptors = Object.keys(source).reduce(function (descriptors, key) {
        descriptors[key] = Object.getOwnPropertyDescriptor(source, key);
        return descriptors;
      }, {});

      Object.getOwnPropertySymbols(source).forEach(function (sym) {
        var descriptor = Object.getOwnPropertyDescriptor(source, sym);
        if (descriptor.enumerable) {
          descriptors[sym] = descriptor;
        }
      });
      Object.defineProperties(target, descriptors);
    });
    return target;
  };

  api.analytics = completeAssign(analytics, {});

  var Type$1 = {
    // impression
    IMPRESSION: {
      id: 'impression', // element appeared in the page
      mode: 'in',
      binding: false,
      type: 'impression'
    },
    // interaction
    CLICK: {
      id: 'click', // generic click interaction
      mode: 'out',
      binding: true,
      type: 'interaction',
      event: 'click',
      method: 'eventListener'
    },
    INTERNAL: {
      id: 'internal', // anchor click redirecting on an internal url
      mode: 'out',
      binding: true,
      type: 'interaction',
      event: 'click',
      method: 'eventListener'
    },
    EXTERNAL: {
      id: 'external', // anchor click redirecting on an external url
      mode: 'out',
      binding: true,
      type: 'interaction',
      event: 'click',
      method: 'eventListener'
    },
    DOWNLOAD: {
      id: 'download', // anchor click downloading a file
      mode: 'out',
      binding: true,
      type: 'interaction',
      event: 'click',
      method: 'eventListener'
    },
    BUTTON: {
      id: 'button', // button click
      mode: 'out',
      binding: true,
      type: 'interaction',
      event: 'click',
      method: 'eventListener'
    },
    DOUBLE_CLICK: {
      id: 'dblclick', // double click
      mode: 'out',
      binding: true,
      type: 'interaction',
      event: 'dblclick',
      method: 'eventListener'
    },
    // event
    OPEN: {
      id: 'open', // open event
      mode: null,
      binding: false,
      type: 'event',
      method: 'eventListener'
    },
    COMPLETE: {
      id: 'complete', // complete event
      mode: null,
      binding: false,
      type: 'event',
      method: 'eventListener'
    },
    FOCUS: {
      id: 'focus', // focus event
      mode: null,
      binding: false,
      type: 'event',
      method: 'eventListener'
    },
    ERROR: {
      id: 'error', // error event
      mode: null,
      binding: false,
      type: 'event'
    },
    ADD: {
      id: 'add', // add event
      mode: null,
      binding: false,
      type: 'event'
    },
    REMOVE: {
      id: 'remove', // remove event
      mode: null,
      binding: false,
      type: 'event'
    },
    DISPLAY: {
      id: 'display', // display event
      mode: null,
      binding: false,
      type: 'event'
    },
    CHANGE: {
      id: 'change', // input event change
      mode: 'out',
      binding: true,
      type: 'event',
      event: 'change',
      method: 'change'
    },
    PROGRESS: {
      id: 'progress', // video retention event with percent of the part reached
      mode: 'out',
      binding: true,
      type: 'event'
    },
    // component interaction
    SHARE: {
      id: 'share', // component share click (share)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    PRESS: {
      id: 'press', // component press click (pressable tag)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    RELEASE: {
      id: 'release', // component release click (pressable tag)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    DISMISS: {
      id: 'dismiss', // component dismiss click (dismissible tag)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    UPLOAD: {
      id: 'upload', // component upload click (upload)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    CHECK: {
      id: 'check', // component check click (checkbox, radio, toggle)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    UNCHECK: {
      id: 'uncheck', // component uncheck click (checkbox, radio, toggle)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    SELECT: {
      id: 'select', // component select change (select)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    SUBSCRIBE: {
      id: 'subscribe', // component subscribe click (follow)
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    // component event
    DISCLOSE: {
      id: 'disclose', // component disclose event (accordion, modal, tab)
      mode: null,
      binding: false,
      type: 'event'
    },
    SHOW: {
      id: 'show', // component show event (tooltip)
      mode: null,
      binding: false,
      type: 'event'
    },
    HIDE: {
      id: 'hide', // component hide event (tooltip)
      mode: null,
      binding: false,
      type: 'event'
    },
    // video
    AUTOPLAY: {
      id: 'autoplay', // video autoplay event
      mode: 'out',
      binding: false,
      type: 'event'
    },
    PLAY: {
      id: 'play', // video play click
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    PAUSE: {
      id: 'pause', // video pause click
      mode: 'out',
      binding: false,
      type: 'interaction'
    },
    END: {
      id: 'end', // video end event
      mode: 'out',
      binding: false,
      type: 'event'
    }
  };

  var Type = {
    UNDEFINED: 'undefined',
    HEADING: 'heading',
    COMPONENT: 'component',
    CONTENT: 'content'
  };

  var NODE_POSITION = Node.DOCUMENT_POSITION_PRECEDING | Node.DOCUMENT_POSITION_CONTAINED_BY;

  var Heading = function Heading (heading) {
    this._label = heading.textContent.trim();
    this._level = Number(heading.tagName.charAt(1));
  };

  var prototypeAccessors$2 = { level: { configurable: true },label: { configurable: true } };

  prototypeAccessors$2.level.get = function () {
    return this._level;
  };

  prototypeAccessors$2.label.get = function () {
    return this._label;
  };

  Object.defineProperties( Heading.prototype, prototypeAccessors$2 );

  var Member = function Member (node, target, level) {
    this._type = Type.UNDEFINED;
    this._node = node;
    this._target = target;
    this._level = level;
    this._label = '';
    this._component = '';
    this._isValid = true;
    this.analyse();
  };

  var prototypeAccessors$1$1 = { type: { configurable: true },level: { configurable: true },label: { configurable: true },component: { configurable: true },node: { configurable: true },target: { configurable: true },isValid: { configurable: true } };

  Member.prototype._parseHeadings = function _parseHeadings () {
      var this$1$1 = this;

    var selector = Array.from({ length: this._level }, function (v, i) { return (":scope > h" + (i + 1) + ", :scope > * > h" + (i + 1)); }).join(',');
    this._headings = [].concat( this._node.querySelectorAll(selector) ).filter(function (heading) { return (this$1$1._target.compareDocumentPosition(heading) & NODE_POSITION) > 0; }).map(function (heading) { return new Heading(heading); }).reverse();
  };

  Member.prototype._getComponent = function _getComponent () {
    if (typeof api !== 'function') { return false; }
    var element = api(this._node);
    if (!element) { return false; }
    var instance = Object.values(element).filter(function (actionee) { return actionee.isActionee; }).sort(function (a, b) { return b.priority - a.priority; })[0];
    if (!instance) { return false; }

    this._type = Type.COMPONENT;
    this._isValid = instance.validate(this._target);
    var selector = Array.from({ length: 6 }, function (v, i) { return ("h" + (i + 1)); }).join(',');
    var heading = this._node.closest(selector);
    if (heading) {
      this._level = Number(heading.tagName.charAt(1)) - 1;
    }
    // console.log('INSTANCE LEVEL', instance.level, this._level);

    if (!isNaN(instance.level) && instance.level < this._level) { this._level = instance.level; }
    this._label = instance.label;
    this._component = instance.component;
    return true;
  };

  Member.prototype._getHeading = function _getHeading () {
      var this$1$1 = this;

    if (!this._headings.length) { return false; }
    var labels = [];
    this._headings.forEach(function (heading) {
      if (heading.level <= this$1$1._level) {
        if (heading.level > 1) { labels.unshift(heading.label); }
        this$1$1._level = heading.level - 1;
      }
    });
    if (!labels.length) { return false; }
    this._type = Type.HEADING;
    this._label = labels.join(' ＞ ');
    return true;
  };

  Member.prototype.analyse = function analyse () {
    this._parseHeadings();
    if (this._getComponent()) { return; }
    if (this._getHeading()) { return; }
    if (this._node !== this._target) { return; }

    var label = this._node.textContent.trim();
    if (!label) { return; }
    this._type = Type.CONTENT;
    this._label = label;
  };

  prototypeAccessors$1$1.type.get = function () {
    return this._type;
  };

  prototypeAccessors$1$1.level.get = function () {
    return this._level;
  };

  prototypeAccessors$1$1.label.get = function () {
    return this._label;
  };

  prototypeAccessors$1$1.component.get = function () {
    return this._component;
  };

  prototypeAccessors$1$1.node.get = function () {
    return this._node;
  };

  prototypeAccessors$1$1.target.get = function () {
    return this._target;
  };

  prototypeAccessors$1$1.isValid.get = function () {
    return this._isValid;
  };

  Object.defineProperties( Member.prototype, prototypeAccessors$1$1 );

  var Hierarchy = function Hierarchy (node) {
    this._node = node;
    this._process();
  };

  var prototypeAccessors$1 = { localComponent: { configurable: true },globalComponent: { configurable: true },label: { configurable: true },title: { configurable: true },component: { configurable: true } };

  Hierarchy.prototype._process = function _process () {
    // console.log('_______________ start ____________________');
    var member = new Member(this._node, this._node, 6);
    // console.log('- FIRST MEMBER', member);
    this._level = member.level;
    this._members = [member];

    var node = this._node.parentNode;

    while (document.documentElement.contains(node) && node !== document.documentElement && this._level > 0) {
      // console.log('MEMBERS ARRAY', this._members);
      // console.log('NODE ANALYSIS', node);
      var member$1 = new Member(node, this._node, this._level);
      // console.log('NEW MEMBER', member);
      switch (true) {
        case member$1.type === Type.UNDEFINED:
          // console.log('****UNDEFINED');
          break;

        case !member$1.isValid:
          // console.log('****INVALID');
          break;

        case member$1.label === this._members[0].label && member$1.type === Type.HEADING && this._members[0].type === Type.COMPONENT:
          // console.log('***** SAME');
          // do nothing
          break;

        case member$1.label === this._members[0].label && member$1.type === Type.COMPONENT && this._members[0].type === Type.HEADING:
          // console.log('***** SAME INVERT');
          this._members.splice(0, 1, member$1);
          break;

        default:
          this._members.unshift(member$1);
          if (member$1.level < this._level) { this._level = member$1.level; }
      }

      node = node.parentNode;
    }

    this._label = normalize(this._members[this._members.length - 1].label);
    this._title = normalize(this._members.filter(function (member) { return member.label; }).map(function (member) { return member.label; }).join(' ＞ '));
    var components = this._members.filter(function (member) { return member.component; }).map(function (member) { return member.component; });
    this._component = normalize(components.join(' ＞ '));
    this._localComponent = components[components.length - 1];
    this._globalComponent = components[0];

    // console.log('========= end ===========');
  };

  prototypeAccessors$1.localComponent.get = function () {
    return this._localComponent;
  };

  prototypeAccessors$1.globalComponent.get = function () {
    return this._globalComponent;
  };

  prototypeAccessors$1.label.get = function () {
    return this._label;
  };

  prototypeAccessors$1.title.get = function () {
    return this._title;
  };

  prototypeAccessors$1.component.get = function () {
    return this._component;
  };

  Object.defineProperties( Hierarchy.prototype, prototypeAccessors$1 );

  var ActionElement = function ActionElement (node, type, id, category, title) {
    if ( category === void 0 ) category = '';
    if ( title === void 0 ) title = null;

    this._node = node;
    this._type = type;
    this._id = id || this._node.id;
    this._isMuted = false;
    this._title = title;
    this._category = category;

    // this._init();
    requestAnimationFrame(this._init.bind(this));
  };

  var prototypeAccessors = { isMuted: { configurable: true },action: { configurable: true } };

  ActionElement.prototype._init = function _init () {
    this._hierarchy = new Hierarchy(this._node);

    var id = '';
    var type = '';
    if (this._id) { id = "_[" + (this._id) + "]"; }
    if (this._type) { type = "_(" + (this._type.id) + ")"; }
    this._name = "" + (this._title || this._hierarchy.title) + id + type;

    this._action = actions.getAction(this._name, true);
    this._action.isMuted = this._isMuted;

    this._action.labels[0] = this._type.id;
    this._action.labels[1] = this._hierarchy.globalComponent;
    this._action.labels[2] = this._hierarchy.localComponent;
    this._action.labels[4] = this._category;

    if (this._hierarchy.label) { this._action.addParameter('component_label', this._hierarchy.label); }
    if (this._hierarchy.title) { this._action.addParameter('heading_hierarchy', this._hierarchy.title); }
    if (this._hierarchy.component) { this._action.addParameter('component_hierarchy', this._hierarchy.component); }
  };

  prototypeAccessors.isMuted.get = function () {
    return this._isMuted;
  };

  prototypeAccessors.isMuted.set = function (value) {
    this._isMuted = value;
    if (this._action) { this.action.isMuted = value; }
  };

  prototypeAccessors.action.get = function () {
    return this._action;
  };

  ActionElement.prototype.act = function act (data) {
      if ( data === void 0 ) data = {};

    var layer = this._action.end(data);
    push(PushType.ACTION, layer);
  };

  ActionElement.prototype.dispose = function dispose () {
    actions.remove(this._action);
  };

  Object.defineProperties( ActionElement.prototype, prototypeAccessors );

  var Actionee = /*@__PURE__*/(function (superclass) {
    function Actionee (type, priority, category, title) {
      if ( type === void 0 ) type = null;
      if ( priority === void 0 ) priority = -1;
      if ( category === void 0 ) category = '';
      if ( title === void 0 ) title = null;

      superclass.call(this);
      this._type = type;
      this._priority = priority;
      this._category = category;
      this._title = title;
      this._data = {};
    }

    if ( superclass ) Actionee.__proto__ = superclass;
    Actionee.prototype = Object.create( superclass && superclass.prototype );
    Actionee.prototype.constructor = Actionee;

    var prototypeAccessors = { proxy: { configurable: true },isMuted: { configurable: true },actionElement: { configurable: true },label: { configurable: true },priority: { configurable: true },isActionee: { configurable: true },level: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'Actionee';
    };

    prototypeAccessors.proxy.get = function () {
      var scope = this;

      var proxy = {
        validate: function (target, members) { return scope.validate(target, members); }
      };

      var proxyAccessors = {
        get isActionee () {
          return true;
        },
        get label () {
          return scope.label;
        },
        get priority () {
          return scope.priority;
        },
        get level () {
          return scope.level;
        },
        get node () {
          return scope.node; // TODO: remove in v2
        }
      };

      return api.internals.property.completeAssign.call(this, superclass.prototype.proxy, proxy, proxyAccessors);
    };

    Actionee.prototype.listenClick = function listenClick () {
      this.listen('click', this.handleClick.bind(this), { capture: true });
    };

    Actionee.prototype.handleClick = function handleClick () {
      this.act();
    };

    Actionee.prototype._config = function _config (element, registration) {
      superclass.prototype._config.call(this, element, registration);
      if (this._type !== null) { this._actionElement = new ActionElement(this.node, this._type, this.id, this._category, this._title); }

      var actionees = element.instances.filter(function (instance) { return instance.isActionee; }).sort(function (a, b) { return b.priority - a.priority; });
      if (actionees.length <= 1) { return; }
      actionees.forEach(function (actionee, index) { actionee.isMuted = index > 0; });
    };

    prototypeAccessors.isMuted.get = function () {
      return !this._actionElement && this._actionElement.isMuted;
    };

    prototypeAccessors.isMuted.set = function (value) {
      if (this._actionElement) { this._actionElement.isMuted = value; }
    };

    Actionee.prototype.detectInteraction = function detectInteraction (node) {
      if (!node) { node = this.node; }
      var tag = node.tagName.toLowerCase();
      var href = node.getAttribute('href');
      var target = node.getAttribute('target');
      var isDownload = node.hasAttribute('download');

      switch (true) {
        case tag === 'a' && isDownload:
          this._type = Type$1.DOWNLOAD;
          this._data.component_value = href;
          break;

        case tag === 'a' && typeof target === 'string' && target.toLowerCase() === '_blank':
          this._type = Type$1.EXTERNAL;
          this._data.component_value = href;
          break;

        case tag === 'a':
          this._type = Type$1.INTERNAL;
          this._data.component_value = href;
          break;

        default:
          this._type = Type$1.CLICK;
      }
    };

    Actionee.prototype.act = function act (data) {
      if ( data === void 0 ) data = {};

      if (this._actionElement !== undefined) { this._actionElement.act(Object.assign(this._data, data)); }
    };

    Actionee.prototype.getInteractionLabel = function getInteractionLabel () {
      var title = this.getAttribute('title');
      if (title) { return title; }

      var content = this.node.textContent.trim();
      if (content) { return content; }

      var img = this.node.querySelector('img');
      if (img) { return img.getAttribute('alt').trim(); }

      return null;
    };

    Actionee.prototype.detectLevel = function detectLevel (node) {
      if (!node) { node = this.node; }
      var selector = Array.from({ length: 6 }, function (v, i) { return ("h" + (i + 1)); }).join(',');
      var levels = [].concat( node.querySelectorAll(selector) ).map(function (heading) { return Number(heading.tagName.charAt(1)); });
      if (levels.length) { this._level = Math.min.apply(null, levels) - 1; }
    };

    Actionee.prototype.validate = function validate (target) {
      return true;
    };

    prototypeAccessors.actionElement.get = function () {
      return this._actionElement;
    };

    prototypeAccessors.label.get = function () {
      return null;
    };

    prototypeAccessors.priority.get = function () {
      return this._priority;
    };

    prototypeAccessors.isActionee.get = function () {
      return true;
    };

    prototypeAccessors.level.get = function () {
      return this._level;
    };

    Object.defineProperties( Actionee.prototype, prototypeAccessors );
    Object.defineProperties( Actionee, staticAccessors );

    return Actionee;
  }(api.core.Instance));

  var AttributeActionee = /*@__PURE__*/(function (Actionee) {
    function AttributeActionee () {
      Actionee.call(this, null, 100);
    }

    if ( Actionee ) AttributeActionee.__proto__ = Actionee;
    AttributeActionee.prototype = Object.create( Actionee && Actionee.prototype );
    AttributeActionee.prototype.constructor = AttributeActionee;

    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'AttributeActionee';
    };

    AttributeActionee.prototype.init = function init () {
      this._attribute = this.registration.selector.replace(/[[\]]/g, '');
      var id = this._attribute.split('-').pop();
      this._type = Object.values(Type$1).filter(function (type) { return type.id === id; })[0];

      this._title = this.getAttribute(this._attribute);

      switch (this._type.method) {
        case 'eventListener':
          this.listen(this._type.event, this.handleEvent.bind(this));
          break;

        case 'change':
          this.listen(this._type.event, this.handleChange.bind(this));
          break;
      }
    };

    AttributeActionee.prototype.handleEvent = function handleEvent (e) {
      this._actionElement.act();
    };

    AttributeActionee.prototype.handleChange = function handleChange (e) {
      this._actionElement.act({ change_value: e.target.value });
    };

    AttributeActionee.prototype.dispose = function dispose () {
      this._actionElement.dispose();
      Actionee.prototype.dispose.call(this);
    };

    Object.defineProperties( AttributeActionee, staticAccessors );

    return AttributeActionee;
  }(Actionee));

  Object.values(Type$1)
    .filter(function (type) { return type.binding; })
    .forEach(function (type) { return api.internals.register(api.internals.ns.attr.selector(("analytics-" + (type.id))), AttributeActionee); });

  var ComponentActionee = /*@__PURE__*/(function (Actionee) {
    function ComponentActionee (type, priority) {
      if ( type === void 0 ) type = null;
      if ( priority === void 0 ) priority = -1;

      Actionee.call(this, type, priority, 'dsfr_component');
    }

    if ( Actionee ) ComponentActionee.__proto__ = Actionee;
    ComponentActionee.prototype = Object.create( Actionee && Actionee.prototype );
    ComponentActionee.prototype.constructor = ComponentActionee;

    var prototypeAccessors = { proxy: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'ComponentActionee';
    };

    prototypeAccessors.proxy.get = function () {
      var scope = this;

      var proxyAccessors = {
        get component () {
          return scope.component;
        }
      };

      return api.internals.property.completeAssign.call(this, Actionee.prototype.proxy, proxyAccessors);
    };

    ComponentActionee.prototype.listenDisclose = function listenDisclose () {
      this.listen(api.core.DisclosureEvent.DISCLOSE, this.handleDisclose.bind(this), { capture: true });
    };

    ComponentActionee.prototype.handleDisclose = function handleDisclose () {
      this.act();
    };

    ComponentActionee.prototype.listenCheckable = function listenCheckable () {
      this.listen('change', this.handleCheckable.bind(this), { capture: true });
    };

    ComponentActionee.prototype.handleCheckable = function handleCheckable (e) {
      if (e.target && e.target.value !== 'on') {
        this._data.component_value = e.target.value;
      }

      switch (true) {
        case this._type === Type$1.CHECK && e.target.checked:
        case this._type === Type$1.UNCHECK && !e.target.checked:
          this.act();
          break;
      }
    };

    ComponentActionee.prototype.detectCheckable = function detectCheckable () {
      var isChecked = this.node.checked;
      this._type = isChecked ? Type$1.UNCHECK : Type$1.CHECK;
    };

    prototypeAccessors.component.get = function () {
      return null;
    };

    Object.defineProperties( ComponentActionee.prototype, prototypeAccessors );
    Object.defineProperties( ComponentActionee, staticAccessors );

    return ComponentActionee;
  }(Actionee));

  var AccordionSelector = {
    ACCORDION: api.internals.ns.selector('accordion'),
    TITLE: api.internals.ns.selector('accordion__title')
  };

  var ID$i = 'dsfr_accordion';

  var AccordionButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function AccordionButtonActionee () {
      ComponentActionee.call(this, Type$1.CLICK, 2);
    }

    if ( ComponentActionee ) AccordionButtonActionee.__proto__ = ComponentActionee;
    AccordionButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    AccordionButtonActionee.prototype.constructor = AccordionButtonActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'AccordionButtonActionee';
    };

    AccordionButtonActionee.prototype.init = function init () {
      this.id = this.node.id || this.registration.creator.node.id;
      this._button = this.element.getInstance('CollapseButton');
      this.listenClick();
    };

    AccordionButtonActionee.prototype.handleClick = function handleClick () {
      if (!this._button.disclosed) { this.act(); }
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$i;
    };

    Object.defineProperties( AccordionButtonActionee.prototype, prototypeAccessors );
    Object.defineProperties( AccordionButtonActionee, staticAccessors );

    return AccordionButtonActionee;
  }(ComponentActionee));

  var AccordionActionee = /*@__PURE__*/(function (ComponentActionee) {
    function AccordionActionee () {
      ComponentActionee.call(this, Type$1.DISCLOSE, 2);
    }

    if ( ComponentActionee ) AccordionActionee.__proto__ = ComponentActionee;
    AccordionActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    AccordionActionee.prototype.constructor = AccordionActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'AccordionActionee';
    };

    AccordionActionee.prototype.init = function init () {
      this.wrapper = this.node.closest(AccordionSelector.ACCORDION);
      this.detectLevel(this.wrapper);
      this.register(("[aria-controls=\"" + (this.id) + "\"]"), AccordionButtonActionee);
      this._instance = this.element.getInstance('Collapse');
      this.listenDisclose();
    };

    prototypeAccessors.label.get = function () {
      if (this.wrapper) {
        var title = this.wrapper.querySelector(AccordionSelector.TITLE);
        if (title) { return title.textContent.trim(); }
      }
      var button = this._instance.buttons.filter(function (button) { return button.isPrimary; })[0];
      if (button) { return button.node.textContent.trim(); }
      return null;
    };

    prototypeAccessors.component.get = function () {
      return ID$i;
    };

    Object.defineProperties( AccordionActionee.prototype, prototypeAccessors );
    Object.defineProperties( AccordionActionee, staticAccessors );

    return AccordionActionee;
  }(ComponentActionee));

  var BreadcrumbSelector = {
    LINK: api.internals.ns.selector('breadcrumb__link'),
    COLLAPSE: ((api.internals.ns.selector('breadcrumb')) + " " + (api.internals.ns.selector('collapse')))
  };

  var BreadcrumbButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function BreadcrumbButtonActionee () {
      ComponentActionee.call(this, Type$1.CLICK, 2);
    }

    if ( ComponentActionee ) BreadcrumbButtonActionee.__proto__ = ComponentActionee;
    BreadcrumbButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    BreadcrumbButtonActionee.prototype.constructor = BreadcrumbButtonActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'BreadcrumbButtonActionee';
    };

    BreadcrumbButtonActionee.prototype.init = function init () {
      this.id = this.node.id || this.registration.creator.node.id;
      this._button = this.element.getInstance('BreadcrumbButton');
      this.listenClick();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return null;
    };

    Object.defineProperties( BreadcrumbButtonActionee.prototype, prototypeAccessors );
    Object.defineProperties( BreadcrumbButtonActionee, staticAccessors );

    return BreadcrumbButtonActionee;
  }(ComponentActionee));

  var ID$h = 'dsfr_breadcrumb';

  var BreadcrumbActionee = /*@__PURE__*/(function (ComponentActionee) {
    function BreadcrumbActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION, 2);
    }

    if ( ComponentActionee ) BreadcrumbActionee.__proto__ = ComponentActionee;
    BreadcrumbActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    BreadcrumbActionee.prototype.constructor = BreadcrumbActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'BreadcrumbActionee';
    };

    BreadcrumbActionee.prototype.init = function init () {
      if (!this.isBreakpoint(api.core.Breakpoints.MD)) {
        this.register(("[aria-controls=\"" + (this.id) + "\"]"), BreadcrumbButtonActionee);
        this.listenDisclose();
      }
    };

    BreadcrumbActionee.prototype.handleDisclose = function handleDisclose () {
      this.act();
    };

    prototypeAccessors.label.get = function () {
      return 'fil d\'ariane';
    };

    prototypeAccessors.component.get = function () {
      return ID$h;
    };

    Object.defineProperties( BreadcrumbActionee.prototype, prototypeAccessors );
    Object.defineProperties( BreadcrumbActionee, staticAccessors );

    return BreadcrumbActionee;
  }(ComponentActionee));

  var BreadcrumbLinkActionee = /*@__PURE__*/(function (ComponentActionee) {
    function BreadcrumbLinkActionee () {
      ComponentActionee.call(this, null, 2);
    }

    if ( ComponentActionee ) BreadcrumbLinkActionee.__proto__ = ComponentActionee;
    BreadcrumbLinkActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    BreadcrumbLinkActionee.prototype.constructor = BreadcrumbLinkActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'BreadcrumbLinkActionee';
    };

    BreadcrumbLinkActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    BreadcrumbLinkActionee.prototype.handleClick = function handleClick () {
      this.act();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return null;
    };

    Object.defineProperties( BreadcrumbLinkActionee.prototype, prototypeAccessors );
    Object.defineProperties( BreadcrumbLinkActionee, staticAccessors );

    return BreadcrumbLinkActionee;
  }(ComponentActionee));

  var ButtonSelector = {
    BUTTON: api.internals.ns.selector('btn')
  };

  var ID$g = 'dsfr_button';

  var ButtonEmission = {
    GET_DATA: api.internals.ns.emission('button', 'get-data')
  };

  var ButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function ButtonActionee () {
      ComponentActionee.call(this, null, 1);
      this._data = {};
    }

    if ( ComponentActionee ) ButtonActionee.__proto__ = ComponentActionee;
    ButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    ButtonActionee.prototype.constructor = ButtonActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'ButtonActionee';
    };

    ButtonActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    ButtonActionee.prototype.handleClick = function handleClick () {
      /* GET_DATA permet d'aller retrouver search_terms dans la search-bar */
      var data = this.ascend(ButtonEmission.GET_DATA);
      this.act(Object.assign.apply(Object, [ {} ].concat( data )));
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$g;
    };

    Object.defineProperties( ButtonActionee.prototype, prototypeAccessors );
    Object.defineProperties( ButtonActionee, staticAccessors );

    return ButtonActionee;
  }(ComponentActionee));

  var CalloutSelector = {
    CALLOUT: api.internals.ns.selector('callout'),
    TITLE: api.internals.ns.selector('callout__title')
  };

  var ID$f = 'dsfr_callout';

  var CalloutActionee = /*@__PURE__*/(function (ComponentActionee) {
    function CalloutActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION, 1);
    }

    if ( ComponentActionee ) CalloutActionee.__proto__ = ComponentActionee;
    CalloutActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    CalloutActionee.prototype.constructor = CalloutActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'CalloutActionee';
    };

    prototypeAccessors.label.get = function () {
      var calloutTitle = this.node.querySelector(CalloutSelector.TITLE);
      if (calloutTitle) { return calloutTitle.textContent.trim(); }

      return 'Mise en avant';
    };

    prototypeAccessors.component.get = function () {
      return ID$f;
    };

    Object.defineProperties( CalloutActionee.prototype, prototypeAccessors );
    Object.defineProperties( CalloutActionee, staticAccessors );

    return CalloutActionee;
  }(ComponentActionee));

  var CardSelector = {
    CARD: api.internals.ns.selector('card'),
    LINK: ((api.internals.ns.selector('card__title')) + " a"),
    TITLE: api.internals.ns.selector('card__title')
  };

  var ID$e = 'dsfr_card';

  var CardActionee = /*@__PURE__*/(function (ComponentActionee) {
    function CardActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION);
      this.handlingClick = this.handleClick.bind(this);
    }

    if ( ComponentActionee ) CardActionee.__proto__ = ComponentActionee;
    CardActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    CardActionee.prototype.constructor = CardActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'CardActionee';
    };

    CardActionee.prototype.init = function init () {
      var link = this.node.querySelector(CardSelector.LINK);
      if (link) {
        this.link = link;
        this.detectInteraction(link);
        this.link.addEventListener('click', this.handlingClick, { capture: true });
      }
    };

    prototypeAccessors.label.get = function () {
      var this$1$1 = this;

      var cardTitle = this.node.querySelector(CardSelector.TITLE);
      if (cardTitle) { return cardTitle.textContent.trim(); }

      var selector = Array.from({ length: 6 }, function (v, i) { return ("h" + (i + 1)); }).join(',');
      var headings = this.node.querySelector(selector) ? [].concat( this.node.querySelector(selector) ).filter(function (heading) { return (this$1$1.node.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_CONTAINED_BY) > 0; }) : [];
      if (headings.length) { return headings[0].textContent.trim(); }

      return null;
    };

    prototypeAccessors.component.get = function () {
      return ID$e;
    };

    CardActionee.prototype.dispose = function dispose () {
      if (this.link) { this.link.removeEventListener('click', this.handlingClick, { capture: true }); }
      ComponentActionee.prototype.dispose.call(this);
    };

    Object.defineProperties( CardActionee.prototype, prototypeAccessors );
    Object.defineProperties( CardActionee, staticAccessors );

    return CardActionee;
  }(ComponentActionee));

  var CheckboxSelector = {
    INPUT: api.internals.ns.selector('checkbox-group [type="checkbox"]')
  };

  var ID$d = 'dsfr_checkbox';

  var CheckboxActionee = /*@__PURE__*/(function (ComponentActionee) {
    function CheckboxActionee () {
      ComponentActionee.call(this, null, 1);
      this._data = {};
    }

    if ( ComponentActionee ) CheckboxActionee.__proto__ = ComponentActionee;
    CheckboxActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    CheckboxActionee.prototype.constructor = CheckboxActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'CheckboxActionee';
    };

    CheckboxActionee.prototype.init = function init () {
      this.detectCheckable();
      this.listenCheckable();
    };

    prototypeAccessors.label.get = function () {
      var label = this.node.parentNode.querySelector(api.internals.ns.selector('label'));
      return label.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$d;
    };

    Object.defineProperties( CheckboxActionee.prototype, prototypeAccessors );
    Object.defineProperties( CheckboxActionee, staticAccessors );

    return CheckboxActionee;
  }(ComponentActionee));

  var FooterSelector = {
    FOOTER: api.internals.ns.selector('footer'),
    FOOTER_LINKS: ((api.internals.ns.selector('footer__content-link')) + ", " + (api.internals.ns.selector('footer__bottom-link')) + ", " + (api.internals.ns.selector('footer__top-link')) + ", " + (api.internals.ns.selector('footer__partners-link')))
  };

  var ID$c = 'dsfr_footer';

  var FooterActionee = /*@__PURE__*/(function (ComponentActionee) {
    function FooterActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION);
    }

    if ( ComponentActionee ) FooterActionee.__proto__ = ComponentActionee;
    FooterActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    FooterActionee.prototype.constructor = FooterActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'FooterActionee';
    };

    prototypeAccessors.label.get = function () {
      return 'Pied de page';
    };

    prototypeAccessors.component.get = function () {
      return ID$c;
    };

    Object.defineProperties( FooterActionee.prototype, prototypeAccessors );
    Object.defineProperties( FooterActionee, staticAccessors );

    return FooterActionee;
  }(ComponentActionee));

  var FooterLinkActionee = /*@__PURE__*/(function (ComponentActionee) {
    function FooterLinkActionee () {
      ComponentActionee.call(this, Type$1.INTERNAL, 2);
    }

    if ( ComponentActionee ) FooterLinkActionee.__proto__ = ComponentActionee;
    FooterLinkActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    FooterLinkActionee.prototype.constructor = FooterLinkActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'FooterLinkActionee';
    };

    FooterLinkActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    prototypeAccessors.label.get = function () {
      return this.getInteractionLabel();
    };

    Object.defineProperties( FooterLinkActionee.prototype, prototypeAccessors );
    Object.defineProperties( FooterLinkActionee, staticAccessors );

    return FooterLinkActionee;
  }(ComponentActionee));

  var ID$b = 'dsfr_header';

  var HeaderActionee = /*@__PURE__*/(function (ComponentActionee) {
    function HeaderActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION);
    }

    if ( ComponentActionee ) HeaderActionee.__proto__ = ComponentActionee;
    HeaderActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    HeaderActionee.prototype.constructor = HeaderActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'HeaderActionee';
    };

    prototypeAccessors.label.get = function () {
      return 'En-tête';
    };

    prototypeAccessors.component.get = function () {
      return ID$b;
    };

    Object.defineProperties( HeaderActionee.prototype, prototypeAccessors );
    Object.defineProperties( HeaderActionee, staticAccessors );

    return HeaderActionee;
  }(ComponentActionee));

  var HeaderSelector = {
    TOOLS_BUTTON: ((api.internals.ns.selector('header__tools-links')) + " " + (api.internals.ns.selector('btns-group')) + " " + (api.internals.ns.selector('btn'))),
    MENU_BUTTON: ((api.internals.ns.selector('header__menu-links')) + " " + (api.internals.ns.selector('btns-group')) + " " + (api.internals.ns.selector('btn')))
  };

  var HeaderModalButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function HeaderModalButtonActionee () {
      ComponentActionee.call(this, null, 4);
    }

    if ( ComponentActionee ) HeaderModalButtonActionee.__proto__ = ComponentActionee;
    HeaderModalButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    HeaderModalButtonActionee.prototype.constructor = HeaderModalButtonActionee;

    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'HeaderModalButtonActionee';
    };

    Object.defineProperties( HeaderModalButtonActionee, staticAccessors );

    return HeaderModalButtonActionee;
  }(ComponentActionee));

  var HeaderModalActionee = /*@__PURE__*/(function (ComponentActionee) {
    function HeaderModalActionee () {
      ComponentActionee.call(this, null, 0);
    }

    if ( ComponentActionee ) HeaderModalActionee.__proto__ = ComponentActionee;
    HeaderModalActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    HeaderModalActionee.prototype.constructor = HeaderModalActionee;

    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'HeaderModalActionee';
    };

    HeaderModalActionee.prototype.init = function init () {
      if (this.isBreakpoint(api.core.Breakpoints.LG)) {
        this._priority = 4;
        this.register(("[aria-controls=\"" + (this.id) + "\"]"), HeaderModalButtonActionee);
      }
    };

    Object.defineProperties( HeaderModalActionee, staticAccessors );

    return HeaderModalActionee;
  }(ComponentActionee));

  var HeaderToolsButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function HeaderToolsButtonActionee () {
      ComponentActionee.call(this, null, 4);
    }

    if ( ComponentActionee ) HeaderToolsButtonActionee.__proto__ = ComponentActionee;
    HeaderToolsButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    HeaderToolsButtonActionee.prototype.constructor = HeaderToolsButtonActionee;

    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'HeaderToolsButtonActionee';
    };

    HeaderToolsButtonActionee.prototype.init = function init () {
      if (this.isBreakpoint(api.core.Breakpoints.LG)) { this._priority = -1; }
    };

    Object.defineProperties( HeaderToolsButtonActionee, staticAccessors );

    return HeaderToolsButtonActionee;
  }(ComponentActionee));

  var HeaderMenuButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function HeaderMenuButtonActionee () {
      ComponentActionee.apply(this, arguments);
    }

    if ( ComponentActionee ) HeaderMenuButtonActionee.__proto__ = ComponentActionee;
    HeaderMenuButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    HeaderMenuButtonActionee.prototype.constructor = HeaderMenuButtonActionee;

    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'HeaderMenuButtonActionee';
    };

    HeaderMenuButtonActionee.prototype.init = function init () {
      if (this.isBreakpoint(api.core.Breakpoints.LG)) { this._priority = 4; }
    };

    Object.defineProperties( HeaderMenuButtonActionee, staticAccessors );

    return HeaderMenuButtonActionee;
  }(ComponentActionee));

  var HighlightSelector = {
    HIGHLIGHT: api.internals.ns.selector('highlight')
  };

  var ID$a = 'dsfr_highlight';

  var HighlightActionee = /*@__PURE__*/(function (ComponentActionee) {
    function HighlightActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION, 1);
    }

    if ( ComponentActionee ) HighlightActionee.__proto__ = ComponentActionee;
    HighlightActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    HighlightActionee.prototype.constructor = HighlightActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'HighlightActionee';
    };

    prototypeAccessors.label.get = function () {
      return 'Mise en exergue';
    };

    prototypeAccessors.component.get = function () {
      return ID$a;
    };

    Object.defineProperties( HighlightActionee.prototype, prototypeAccessors );
    Object.defineProperties( HighlightActionee, staticAccessors );

    return HighlightActionee;
  }(ComponentActionee));

  var LinkSelector = {
    LINK: api.internals.ns.selector('link')
  };

  var ID$9 = 'dsfr_link';

  var LinkActionee = /*@__PURE__*/(function (ComponentActionee) {
    function LinkActionee () {
      ComponentActionee.call(this, Type$1.INTERNAL, 1);
    }

    if ( ComponentActionee ) LinkActionee.__proto__ = ComponentActionee;
    LinkActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    LinkActionee.prototype.constructor = LinkActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'LinkActionee';
    };

    LinkActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$9;
    };

    Object.defineProperties( LinkActionee.prototype, prototypeAccessors );
    Object.defineProperties( LinkActionee, staticAccessors );

    return LinkActionee;
  }(ComponentActionee));

  var NavigationSelector = {
    LINK: api.internals.ns.selector('nav__link'),
    BUTTON: api.internals.ns.selector('nav__btn')
  };

  var NavigationActionee = /*@__PURE__*/(function (ComponentActionee) {
    function NavigationActionee () {
      ComponentActionee.call(this, null, 1);
    }

    if ( ComponentActionee ) NavigationActionee.__proto__ = ComponentActionee;
    NavigationActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    NavigationActionee.prototype.constructor = NavigationActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'NavigationActionee';
    };

    prototypeAccessors.label.get = function () {
      return 'Navigation';
    };

    Object.defineProperties( NavigationActionee.prototype, prototypeAccessors );
    Object.defineProperties( NavigationActionee, staticAccessors );

    return NavigationActionee;
  }(ComponentActionee));

  var NavigationSectionActionee = /*@__PURE__*/(function (ComponentActionee) {
    function NavigationSectionActionee () {
      ComponentActionee.call(this, null, 2);
    }

    if ( ComponentActionee ) NavigationSectionActionee.__proto__ = ComponentActionee;
    NavigationSectionActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    NavigationSectionActionee.prototype.constructor = NavigationSectionActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'NavigationSectionActionee';
    };

    NavigationSectionActionee.prototype.init = function init () {
      this._wrapper = this.node.closest(api.navigation.NavigationSelector.ITEM);
      this._instance = this.element.getInstance('Collapse');
    };

    prototypeAccessors.label.get = function () {
      if (this._wrapper) {
        var button$1 = this._wrapper.querySelector(NavigationSelector.BUTTON);
        if (button$1) { return button$1.textContent.trim(); }
      }
      var button = this._instance.buttons.filter(function (button) { return button.isPrimary; })[0];
      if (button) { return button.node.textContent.trim(); }
      return null;
    };

    Object.defineProperties( NavigationSectionActionee.prototype, prototypeAccessors );
    Object.defineProperties( NavigationSectionActionee, staticAccessors );

    return NavigationSectionActionee;
  }(ComponentActionee));

  var ID$8 = 'dsfr_navigation';

  var NavigationLinkActionee = /*@__PURE__*/(function (ComponentActionee) {
    function NavigationLinkActionee () {
      ComponentActionee.call(this, null, 2);
    }

    if ( ComponentActionee ) NavigationLinkActionee.__proto__ = ComponentActionee;
    NavigationLinkActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    NavigationLinkActionee.prototype.constructor = NavigationLinkActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'NavigationLinkActionee';
    };

    NavigationLinkActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$8;
    };

    Object.defineProperties( NavigationLinkActionee.prototype, prototypeAccessors );
    Object.defineProperties( NavigationLinkActionee, staticAccessors );

    return NavigationLinkActionee;
  }(ComponentActionee));

  var ModalSelector = {
    TITLE: api.internals.ns.selector('modal__title')
  };

  var ID$7 = 'dsfr_modal';

  var ModalActionee = /*@__PURE__*/(function (ComponentActionee) {
    function ModalActionee () {
      ComponentActionee.call(this, Type$1.DISCLOSE, 2);
    }

    if ( ComponentActionee ) ModalActionee.__proto__ = ComponentActionee;
    ModalActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    ModalActionee.prototype.constructor = ModalActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'ModalActionee';
    };

    ModalActionee.prototype.init = function init () {
      this.detectLevel();
      this.listenDisclose();
    };

    prototypeAccessors.label.get = function () {
      var this$1$1 = this;

      var title = this.node.querySelector(ModalSelector.TITLE);

      if (title) { return title.textContent.trim(); }

      var selector = Array.from({ length: 2 }, function (v, i) { return ("h" + (i + 1)); }).join(',');
      var headings = this.node.querySelector(selector) ? [].concat( this.node.querySelector(selector) ).filter(function (heading) { return (this$1$1.node.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_CONTAINED_BY) > 0; }) : [];

      if (headings.length) { return headings[0].textContent.trim(); }

      var button = this.element.getInstance('Modal').buttons.filter(function (button) { return button.isPrimary; })[0];
      return button.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$7;
    };

    Object.defineProperties( ModalActionee.prototype, prototypeAccessors );
    Object.defineProperties( ModalActionee, staticAccessors );

    return ModalActionee;
  }(ComponentActionee));

  var RadioSelector = {
    INPUT: api.internals.ns.selector('radio-group [type="radio"]')
  };

  var FormSelector = {
    LABEL: api.internals.ns.selector('label'),
    FIELDSET: api.internals.ns.selector('fieldset'),
    LEGEND: api.internals.ns.selector('fieldset__legend')
  };

  var ID$6 = 'dsfr_radio';

  var RadioActionee = /*@__PURE__*/(function (ComponentActionee) {
    function RadioActionee () {
      ComponentActionee.call(this, Type$1.CHECK, 1);
      this._data = {};
    }

    if ( ComponentActionee ) RadioActionee.__proto__ = ComponentActionee;
    RadioActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    RadioActionee.prototype.constructor = RadioActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'RadioActionee';
    };

    RadioActionee.prototype.init = function init () {
      this.listenCheckable();
    };

    prototypeAccessors.label.get = function () {
      var parts = [];
      var fieldset = this.node.closest(FormSelector.FIELDSET);
      if (fieldset) {
        var legend = fieldset.querySelector(FormSelector.LEGEND);
        if (legend) { parts.push(legend.textContent.trim()); }
      }
      var label = this.node.parentNode.querySelector(api.internals.ns.selector('label'));
      if (label) { parts.push(label.textContent.trim()); }
      return parts.join(' ＞ ');
    };

    prototypeAccessors.component.get = function () {
      return ID$6;
    };

    Object.defineProperties( RadioActionee.prototype, prototypeAccessors );
    Object.defineProperties( RadioActionee, staticAccessors );

    return RadioActionee;
  }(ComponentActionee));

  var SearchSelector = {
    SEARCH_BAR: api.internals.ns.selector('search-bar')
  };

  var ID$5 = 'dsfr_search';

  var SearchActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SearchActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION);
    }

    if ( ComponentActionee ) SearchActionee.__proto__ = ComponentActionee;
    SearchActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SearchActionee.prototype.constructor = SearchActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SearchActionee';
    };

    SearchActionee.prototype.init = function init () {
      this.addAscent(ButtonEmission.GET_DATA, this.getData.bind(this));
      this._input = this.querySelector('input[type="search"],input[type="text"]');
    };

    SearchActionee.prototype.getData = function getData () {
      return { search_terms: this._input.value };
    };

    prototypeAccessors.label.get = function () {
      return 'barre de recherche';
    };

    prototypeAccessors.component.get = function () {
      return ID$5;
    };

    Object.defineProperties( SearchActionee.prototype, prototypeAccessors );
    Object.defineProperties( SearchActionee, staticAccessors );

    return SearchActionee;
  }(ComponentActionee));

  var SidemenuSelector = {
    SIDEMENU: api.internals.ns.selector('sidemenu'),
    ITEM: api.internals.ns.selector('sidemenu__item'),
    LINK: api.internals.ns.selector('sidemenu__link'),
    BUTTON: api.internals.ns.selector('sidemenu__btn'),
    TITLE: api.internals.ns.selector('sidemenu__title')
  };

  var SidemenuActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SidemenuActionee () {
      ComponentActionee.call(this, null, 1);
    }

    if ( ComponentActionee ) SidemenuActionee.__proto__ = ComponentActionee;
    SidemenuActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SidemenuActionee.prototype.constructor = SidemenuActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SidemenuActionee';
    };

    prototypeAccessors.label.get = function () {
      var sidemenu = this.node.closest(SidemenuSelector.SIDEMENU);
      if (sidemenu) {
        var title = sidemenu.querySelector(SidemenuSelector.TITLE);
        if (title) { return title.textContent.trim(); }
      }

      return 'Menu Latéral';
    };

    Object.defineProperties( SidemenuActionee.prototype, prototypeAccessors );
    Object.defineProperties( SidemenuActionee, staticAccessors );

    return SidemenuActionee;
  }(ComponentActionee));

  var ID$4 = 'dsfr_sidemenu';

  var SidemenuLinkActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SidemenuLinkActionee () {
      ComponentActionee.call(this, null, 2);
    }

    if ( ComponentActionee ) SidemenuLinkActionee.__proto__ = ComponentActionee;
    SidemenuLinkActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SidemenuLinkActionee.prototype.constructor = SidemenuLinkActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SidemenuLinkActionee';
    };

    SidemenuLinkActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$4;
    };

    Object.defineProperties( SidemenuLinkActionee.prototype, prototypeAccessors );
    Object.defineProperties( SidemenuLinkActionee, staticAccessors );

    return SidemenuLinkActionee;
  }(ComponentActionee));

  var SidemenuSectionActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SidemenuSectionActionee () {
      ComponentActionee.call(this, null, 2);
    }

    if ( ComponentActionee ) SidemenuSectionActionee.__proto__ = ComponentActionee;
    SidemenuSectionActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SidemenuSectionActionee.prototype.constructor = SidemenuSectionActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SidemenuSectionActionee';
    };

    SidemenuSectionActionee.prototype.init = function init () {
      this._wrapper = this.node.closest(SidemenuSelector.ITEM);
      this._instance = this.element.getInstance('Collapse');
    };

    prototypeAccessors.label.get = function () {
      if (this._wrapper) {
        var button$1 = this._wrapper.querySelector(SidemenuSelector.BUTTON);
        if (button$1) { return button$1.textContent.trim(); }
      }
      var button = this._instance.buttons.filter(function (button) { return button.isPrimary; })[0];
      if (button) { return button.node.textContent.trim(); }
      return null;
    };

    Object.defineProperties( SidemenuSectionActionee.prototype, prototypeAccessors );
    Object.defineProperties( SidemenuSectionActionee, staticAccessors );

    return SidemenuSectionActionee;
  }(ComponentActionee));

  var ShareSelector = {
    SHARE: api.internals.ns.selector('share'),
    TITLE: api.internals.ns.selector('share__title')
  };

  var ID$3 = 'dsfr_share';

  var ShareActionee = /*@__PURE__*/(function (ComponentActionee) {
    function ShareActionee () {
      ComponentActionee.call(this, Type$1.IMPRESSION, 1);
    }

    if ( ComponentActionee ) ShareActionee.__proto__ = ComponentActionee;
    ShareActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    ShareActionee.prototype.constructor = ShareActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'ShareActionee';
    };

    prototypeAccessors.label.get = function () {
      var title = this.querySelector(ShareSelector.TITLE);
      if (title) { return title.textContent.trim(); }
      return 'Boutons de partage';
    };

    prototypeAccessors.component.get = function () {
      return ID$3;
    };

    Object.defineProperties( ShareActionee.prototype, prototypeAccessors );
    Object.defineProperties( ShareActionee, staticAccessors );

    return ShareActionee;
  }(ComponentActionee));

  var SummarySelector = {
    SUMMARY: api.internals.ns.selector('summary'),
    LINK: api.internals.ns.selector('summary__link'),
    TITLE: api.internals.ns.selector('summary__title'),
    ITEM: ((api.internals.ns.selector('summary')) + " li")
  };

  var SummaryActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SummaryActionee () {
      ComponentActionee.call(this, null, 1);
    }

    if ( ComponentActionee ) SummaryActionee.__proto__ = ComponentActionee;
    SummaryActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SummaryActionee.prototype.constructor = SummaryActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SummaryActionee';
    };

    prototypeAccessors.label.get = function () {
      var title = this.node.querySelector(SummarySelector.TITLE);
      if (title) { return title.textContent.trim(); }
      return 'Sommaire';
    };

    Object.defineProperties( SummaryActionee.prototype, prototypeAccessors );
    Object.defineProperties( SummaryActionee, staticAccessors );

    return SummaryActionee;
  }(ComponentActionee));

  var ID$2 = 'dsfr_summary';

  var SummaryLinkActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SummaryLinkActionee () {
      ComponentActionee.call(this, Type$1.INTERNAL, 1);
    }

    if ( ComponentActionee ) SummaryLinkActionee.__proto__ = ComponentActionee;
    SummaryLinkActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SummaryLinkActionee.prototype.constructor = SummaryLinkActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SummaryLinkActionee';
    };

    SummaryLinkActionee.prototype.init = function init () {
      this.detectInteraction();
      this.listenClick();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$2;
    };

    Object.defineProperties( SummaryLinkActionee.prototype, prototypeAccessors );
    Object.defineProperties( SummaryLinkActionee, staticAccessors );

    return SummaryLinkActionee;
  }(ComponentActionee));

  var SummarySectionActionee = /*@__PURE__*/(function (ComponentActionee) {
    function SummarySectionActionee () {
      ComponentActionee.call(this, null, 2);
    }

    if ( ComponentActionee ) SummarySectionActionee.__proto__ = ComponentActionee;
    SummarySectionActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    SummarySectionActionee.prototype.constructor = SummarySectionActionee;

    var prototypeAccessors = { label: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'SummarySectionActionee';
    };

    SummarySectionActionee.prototype.init = function init () {
      this._link = this.querySelector(SummarySelector.LINK);
    };

    SummarySectionActionee.prototype.validate = function validate (target) {
      return this._link !== target;
    };

    prototypeAccessors.label.get = function () {
      if (!this._link) { return null; }
      return this._link.textContent.trim();
    };

    Object.defineProperties( SummarySectionActionee.prototype, prototypeAccessors );
    Object.defineProperties( SummarySectionActionee, staticAccessors );

    return SummarySectionActionee;
  }(ComponentActionee));

  var ToggleSelector = {
    INPUT: api.internals.ns.selector('toggle [type="checkbox"]')
  };

  var ID$1 = 'dsfr_toggle';

  var ToggleActionee = /*@__PURE__*/(function (ComponentActionee) {
    function ToggleActionee () {
      ComponentActionee.call(this, null, 1);
      this._data = {};
    }

    if ( ComponentActionee ) ToggleActionee.__proto__ = ComponentActionee;
    ToggleActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    ToggleActionee.prototype.constructor = ToggleActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'ToggleActionee';
    };

    ToggleActionee.prototype.init = function init () {
      this.detectCheckable();
      this.listenCheckable();
    };

    prototypeAccessors.label.get = function () {
      var label = this.node.parentNode.querySelector(api.internals.ns.selector('toggle__label'));
      return label.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID$1;
    };

    Object.defineProperties( ToggleActionee.prototype, prototypeAccessors );
    Object.defineProperties( ToggleActionee, staticAccessors );

    return ToggleActionee;
  }(ComponentActionee));

  var ID = 'dsfr_tab';

  var TabButtonActionee = /*@__PURE__*/(function (ComponentActionee) {
    function TabButtonActionee () {
      ComponentActionee.call(this, Type$1.CLICK, 2);
    }

    if ( ComponentActionee ) TabButtonActionee.__proto__ = ComponentActionee;
    TabButtonActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    TabButtonActionee.prototype.constructor = TabButtonActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'TabButtonActionee';
    };

    TabButtonActionee.prototype.init = function init () {
      this.id = this.node.id || this.registration.creator.node.id;
      this._button = this.element.getInstance('TabButton');
      this.listen('click', this.click.bind(this), { capture: true });
    };

    TabButtonActionee.prototype.click = function click () {
      this.act();
    };

    prototypeAccessors.label.get = function () {
      return this.node.textContent.trim();
    };

    prototypeAccessors.component.get = function () {
      return ID;
    };

    Object.defineProperties( TabButtonActionee.prototype, prototypeAccessors );
    Object.defineProperties( TabButtonActionee, staticAccessors );

    return TabButtonActionee;
  }(ComponentActionee));

  var TabActionee = /*@__PURE__*/(function (ComponentActionee) {
    function TabActionee () {
      ComponentActionee.call(this, Type$1.DISCLOSE, 2);
    }

    if ( ComponentActionee ) TabActionee.__proto__ = ComponentActionee;
    TabActionee.prototype = Object.create( ComponentActionee && ComponentActionee.prototype );
    TabActionee.prototype.constructor = TabActionee;

    var prototypeAccessors = { label: { configurable: true },component: { configurable: true } };
    var staticAccessors = { instanceClassName: { configurable: true } };

    staticAccessors.instanceClassName.get = function () {
      return 'TabActionee';
    };

    TabActionee.prototype.init = function init () {
      this.register(("[aria-controls=\"" + (this.id) + "\"]"), TabButtonActionee);
      this._instance = this.element.getInstance('TabPanel');
      this.listenDisclose();
    };

    prototypeAccessors.label.get = function () {
      var tabs = this.node.closest(api.tab.TabSelector.GROUP);
      if (tabs) {
        var tab = tabs.querySelector(((api.tab.TabSelector.LIST) + " [aria-controls=\"" + (this.id) + "\"]" + (api.tab.TabSelector.TAB)));
        if (tab) { return tab.textContent.trim(); }
      }

      var button = this._instance.buttons.filter(function (button) { return button.isPrimary; })[0];
      if (button) { return button.node.textContent.trim(); }
      return null;
    };

    prototypeAccessors.component.get = function () {
      return ID;
    };

    Object.defineProperties( TabActionee.prototype, prototypeAccessors );
    Object.defineProperties( TabActionee, staticAccessors );

    return TabActionee;
  }(ComponentActionee));

  if (api.accordion) {
    api.internals.register(api.accordion.AccordionSelector.COLLAPSE, AccordionActionee);
  }

  if (api.breadcrumb) {
    api.internals.register(BreadcrumbSelector.COLLAPSE, BreadcrumbActionee);
    api.internals.register(BreadcrumbSelector.LINK, BreadcrumbLinkActionee);
  }

  api.internals.register(ButtonSelector.BUTTON, ButtonActionee);

  api.internals.register(CalloutSelector.CALLOUT, CalloutActionee);

  api.internals.register(CardSelector.CARD, CardActionee);

  api.internals.register(CheckboxSelector.INPUT, CheckboxActionee);

  api.internals.register(FooterSelector.FOOTER, FooterActionee);
  api.internals.register(FooterSelector.FOOTER_LINKS, FooterLinkActionee);

  if (api.header) {
    api.internals.register(api.header.HeaderSelector.HEADER, HeaderActionee);
    api.internals.register(api.header.HeaderSelector.MODALS, HeaderModalActionee);
    api.internals.register(HeaderSelector.TOOLS_BUTTON, HeaderToolsButtonActionee);
    api.internals.register(HeaderSelector.MENU_BUTTON, HeaderMenuButtonActionee);
  }

  api.internals.register(HighlightSelector.HIGHLIGHT, HighlightActionee);

  api.internals.register(LinkSelector.LINK, LinkActionee);

  if (api.modal) {
    api.internals.register(api.modal.ModalSelector.MODAL, ModalActionee);
  }

  if (api.navigation) {
    api.internals.register(api.navigation.NavigationSelector.NAVIGATION, NavigationActionee);
    api.internals.register(NavigationSelector.LINK, NavigationLinkActionee);
    api.internals.register(api.navigation.NavigationSelector.COLLAPSE, NavigationSectionActionee);
  }

  api.internals.register(RadioSelector.INPUT, RadioActionee);

  api.internals.register(SearchSelector.SEARCH_BAR, SearchActionee);

  if (api.sidemenu) {
    api.internals.register(SidemenuSelector.SIDEMENU, SidemenuActionee);
    api.internals.register(SidemenuSelector.LINK, SidemenuLinkActionee);
    api.internals.register(api.sidemenu.SidemenuSelector.COLLAPSE, SidemenuSectionActionee);
  }

  api.internals.register(ShareSelector.SHARE, ShareActionee);

  api.internals.register(SummarySelector.SUMMARY, SummaryActionee);
  api.internals.register(SummarySelector.LINK, SummaryLinkActionee);
  api.internals.register(SummarySelector.ITEM, SummarySectionActionee);

  if (api.tab) {
    api.internals.register(api.tab.TabSelector.PANEL, TabActionee);
  }

  api.internals.register(ToggleSelector.INPUT, ToggleActionee);

})();
//# sourceMappingURL=analytics.nomodule.js.map
