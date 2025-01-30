# <span style="font-variant: small-caps;">[Meliag](https://www.gijs6.nl/meliag)</span> <img src="https://www.gijs6.nl/static/meliag/Loogootje.svg" width=50>

From Latin _**meli**us **ag**men_ meaning _better train_ (I hope :D)

A website I am building to display all kinds of data about trains in a 'better' way.

Data from the [NS API](https://apiportal.ns.nl/) and (maybe in the future from [NDOV](https://ndovloket.nl/))?

## Ideas / stuff to add

### Stuff/features to add / stuff to (bug)fix

#### Map

- [ ] Images on the map
- [ ] Filters on the map (_materieel_ and other stuff)
- [ ] Fix images in the popup and the content/layout/styles of the popup
- [ ] More info in popup
- [ ] Station info in popup (current station & stations en route?)

#### _Treintijden_ and the map

- [ ] Fix and combine the _ritnummer_-data for the _treintijden_ and the map!!!

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
- [ ] Responsive design for the _treintijden_ (fix flexbox and div's)
- [ ] Fix bug: the _treintijden_ for the **first** station (in the country [such as _Breda_]) of an international train
  shows that the train started at that station
- [ ] Fix layout for really long trains (and/or just normal trains on mobile)

#### Other

- [ ] Responsive design for menu, homepage and footer

### Pages to add

- [x] Departing / arriving times (per station) + images/drawings (of the trains (so that the _materieel_ clear is))
- [ ] _Spoorkaart_ (the rail lines) with _SpoorKaart API_ (+ disruptions?)
- [ ] Search box for _matnummers_ and _ritnummers_ (-> redirect to /matnummer/{matnum} or /ritnummer/{ritnum})