# Meliag

From Latin ***meli**us **ag**men* meaning *better train* (I hope :D)

A website I am building to display all kinds of data about trains in a 'better' way.

Built with the *amazing* Python framework [Flask](https://github.com/pallets/flask) and the [Jinja](https://github.com/pallets/jinja) templating engine.

Data from the [NS API](https://apiportal.ns.nl/).

## Ideas / stuff to add

### Stuff/features to add / stuff to (bug)fix

#### Map

- [x] Images on the map (semi-fixed)
- [ ] Filters on the map (*materieel* and other stuff)
- [ ] Fix images in the popup and the content/layout/styles of the popup
- [ ] More info in popup
- [ ] Station info in popup (current station & stations en route?)

#### Both *Treintijden* **and** the map

- [x] Fix and combine the *ritnummer*-data for the *treintijden* and the map!!!
- [ ] Fix thread bug *ritnummer*-data and just the ritnumdata in general

#### *Treintijden*

- [x] Adding some better styles to the *treintijden*
- [x] Adding images and more info to the *treintijden*
- [x] Bug with the alt text of the train image with international trains
- [x] Cleaning up delays and other time information
- [x] A menu for the *treintijden* in the menu bar
- [x] Add the 15 biggest stations in the submenu
- [x] Add a redirect/search page for the *treintijden*!
- [x] Nice exit animation for the submenu (with JS?)
- [ ] Add links to the *op de route* (en route) stations in *treintijden* (with UIC?)
- [ ] Responsive design for the *treintijden* (fix flexbox and div's (in the entire row))
- [ ] Fix bug: the *treintijden* for the **first** station (in the country [such as *Breda*]) of an international train
  shows that the train started at that station
- [ ] Fix layout for really long trains (and/or just normal trains on mobile)
- [ ] Fix "no image available" if it occurs many times (such as with the *European Sleeper*)
- [ ] Fix spacing between trains (if the description text is long)
- [ ] Fix no image displayed (probably some bug with the new data system)

#### Other

- [ ] Responsive design for menu, homepage and footer
- [ ] Fix submenu hover on mobile (disable link, make the menu item clickable)
- [x] Fix layout *treintijden* search page on mobile
- [ ] Fix long loading times

### Pages to add

- [x] Departing / arriving times (per station) + images/drawings (of the trains (so that the *materieel* clear is))
- [ ] *Spoorkaart* (the rail lines) with *SpoorKaart API* (+ disruptions?) (-> combining with map?)
- [ ] Search box for *matnummers* and *ritnummers* (-> redirect to /matnummer/{matnum} and/or /ritnummer/{ritnum})
