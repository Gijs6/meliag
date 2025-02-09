# <div style="display:flex;flex-direction:row;gap:10px;align-items:center"><span style="font-variant: small-caps;">[Meliag](https://www.gijs6.nl/meliag)</span> <img src="https://www.gijs6.nl/static/meliag/Loogootje.svg" width=45></div>

From Latin _**meli**us **ag**men_ meaning _better train_ (I hope :D)

A website I am building to display all kinds of data about trains in a 'better' way.

Built with the _amazing_ Python framework [Flask](https://github.com/pallets/flask) and the [Jinja](https://github.com/pallets/jinja) templating engine.

Data from the [NS API](https://apiportal.ns.nl/).

## Ideas / stuff to add

### Stuff/features to add / stuff to (bug)fix

#### Map

- [x] Images on the map (semi-fixed)
- [ ] Filters on the map (_materieel_ and other stuff)
- [ ] Fix images in the popup and the content/layout/styles of the popup
- [ ] More info in popup
- [ ] Station info in popup (current station & stations en route?)

#### _Treintijden_ **and** the map

- [x] Fix and combine the _ritnummer_-data for the _treintijden_ and the map!!!
- [ ] Fix thread bug _ritnummer_-data

#### _Treintijden_

- [x] Adding some better styles to the _treintijden_
- [x] Adding images and more info to the _treintijden_
- [x] Bug with the alt text of the train image with international trains
- [x] Cleaning up delays and other time information
- [x] A menu for the _treintijden_ in the menu bar
- [x] Add the 15 biggest stations in the submenu
- [x] Add a redirect/search page for the _treintijden_!
- [x] Nice exit animation for the submenu (with JS?)
- [ ] Add links to the _op de route_ (en route) stations in _treintijden_ (with UIC?)
- [ ] Responsive design for the _treintijden_ (fix flexbox and div's (in the entire row))
- [ ] Fix bug: the _treintijden_ for the **first** station (in the country [such as _Breda_]) of an international train
  shows that the train started at that station
- [ ] Fix layout for really long trains (and/or just normal trains on mobile)
- [ ] Fix "no image available" if it occurs many times (such as with the _European Sleeper_)
- [ ] Fix spacing between trains (if the description text is long)
- [ ] Fix no image displayed (probably some bug with the new data system)

#### Other

- [ ] Responsive design for menu, homepage and footer
- [x] Fix submenu hover on mobile (disable link, make the menu item clickable)
- [x] Fix layout _treintijden_ search page on mobile
- [ ] Fix long loading times

### Pages to add

- [x] Departing / arriving times (per station) + images/drawings (of the trains (so that the _materieel_ clear is))
- [ ] _Spoorkaart_ (the rail lines) with _SpoorKaart API_ (+ disruptions?) (-> combining with map?)
- [ ] Search box for _matnummers_ and _ritnummers_ (-> redirect to /matnummer/{matnum} and/or /ritnummer/{ritnum})