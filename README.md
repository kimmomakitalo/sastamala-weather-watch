# Sastamalan säävahti

Python-ohjelma hakee Open-Meteon maksuttomasta ennuste-API:sta Sastamalan seuraavan 24 tunnin tuntiennusteen. Se arvioi pakkas-, lumisade- ja liukkausriskiä. Kun varoitusehto täyttyy, ohjelma luo GitHub-issueen varoituksen ja sulkee Issuen heti luomisen jälkeen. Ilmoituksia ei lähetetä, jos varoitusehtoja ei täyty.

Säädata ja analysointi eivät kerro todellista teiden kuntoa. Liukkaus on sääennusteeseen perustuva riskinarvio.

## Varoitussäännöt ja asetukset

Raja-arvot löytyvät tiedostosta `weather_watch/config.py`.

* **Pakkanen:** seuraavan 24 tunnin alin tuntiennusteen lämpötila on enintään `-3 °C`.
* **Lumisade:** tuntiennusteen lumisateiden summa on vähintään `2 cm` seuraavan 24 tunnin aikana.
* **Liukkausriski:** varoitus syntyy, kun ennusteessa on vähintään jokin seuraavista:
  * lunta vähintään `0,1 cm` tunnissa ja lämpötila enintään `+2 °C`;
  * vesisadetta vähintään `0,2 mm` tunnissa ja lämpötila enintään `+3 °C` (mukana on myös hieman nollan yläpuolella oleva lämpötila);
  * vesisadetta vähintään `0,2 mm` lämpötilan ollessa yli `0 °C` ja enintään `+4 °C`, minkä jälkeen lämpötila laskee nollaan tai sen alle kuuden tunnin kuluessa.

Liukkausvaroitus kertoo sen synnyttäneet sääolosuhteet ja ajoituksen. Kynnysarvot ovat varovaisia aloitusarvoja, eivät virallisia varoitusrajoja. Ennusteessa käytetään lämpötilaa, vesisadetta, kuurosadetta ja lumisadetta. Säämuuttujien ja riskirajojen muuttaminen onnistuu `config.py`-tiedostossa.

## Open-Meteo ja käyttöehdot

Ohjelma tekee yhden API-pyynnön päivässä Open-Meteon `https://api.open-meteo.com/v1/forecast`-rajapintaan, joten käyttö jää selvästi ilmaisen palvelun ehtosivulla ilmoitetun 10 000 päivittäisen pyynnön rajan alle. API-avainta ei tarvita. Maksuton API on tarkoitettu ei-kaupalliseen käyttöön, ja sen käyttöön sovelletaan Open-Meteon ehtoja ja CC BY 4.0 -lisenssiä. Varoitus-Issueissa on Open-Meteo-attribuutio ja linkki palveluun. Älä käytä tätä ilmaista rajapintaa kaupalliseen tarkoitukseen; tarkista ajantasaiset ehdot ennen käyttöönottoa.

* [Open-Meteo API -dokumentaatio](https://open-meteo.com/en/docs)
* [Open-Meteon käyttöehdot](https://open-meteo.com/en/terms)
* [Open-Meteon lisenssi ja attribuutiovaatimukset](https://open-meteo.com/en/licence)

## Paikallinen asennus ja suoritus

Vaatii Python 3.10:n tai uudemman.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m weather_watch
```

Ilmoitusten lähettämistä varten paikallisessa ympäristössä on asetettava `GITHUB_TOKEN` (oikeus luoda ja sulkea Issueja) sekä `GITHUB_REPOSITORY` muodossa `omistaja/repository`. Älä tallenna tokenia koodiin tai versionhallintaan. Jos varoituksia ei synny, tokenia ei tarvita.

Testit:

```powershell
python -m pytest
```

## GitHub Actionsin käyttöönotto

1. Lisää tämän projektin tiedostot omaan GitHub-repositorioosi ja varmista, että workflow on repositorion oletushaarassa. Säävahti ei luo repositoriota eikä tee pushia.
2. Salli repositorion asetuksissa **Settings → Actions → General → Workflow permissions** workflowjen luoda ja päivittää Issueja (read/write permissions). Workflow rajaa käyttöoikeudet `issues: write`- ja `contents: read`-oikeuksiin.
3. Varmista, että GitHub Actions on käytössä. Avaa **Actions → Sastamalan säävahti → Run workflow** manuaalista ajoa varten.

Workflow käyttää automaattisesti GitHubin `GITHUB_TOKEN`-tunnusta; salaisuuksia ei tarvitse lisätä. Issue-ilmoitusten sähköpostitoimitus riippuu vastaanottajan GitHubin ilmoitusasetuksista ja repositorion seurannasta. Suljettu Issue saattaa silti tuottaa sähköposti-ilmoituksen; GitHubin asetukset ratkaisevat toimituksen.

### Ajastus ja kesäaika

GitHub Actionsin `schedule`-cron tulkitaan UTC-ajassa, eikä sille voi asettaa IANA-aikavyöhykettä. Suomen aika on talvella UTC+2 ja kesällä UTC+3. Workflow käyttää kahta UTC-ajastusta (`13:17` ja `14:17`): kesäajalla klo 13.17 UTC ja talviajalla klo 14.17 UTC osuvat Suomen aikaan klo 16.17. Ohjelma tarkistaa ajastetussa ajossa `Europe/Helsinki`-paikallisajan ja ohittaa väärän ajastuksen. Manuaalinen ajo ei riipu kellonajasta.

Cron-minuutti 17 välttää tasatunnin ruuhkaa, mutta GitHub voi kuormitustilanteissa viivästyttää ajastettuja ajoja; tarkkaa toimitusaikaa ei taata. Luotettavampi vaihtoehto täsmälliselle paikallisajalle olisi ulkoinen ajastin, joka käynnistää GitHub workflow_dispatch -tapahtuman oikealla Suomen kellonajalla, mutta tässä ensimmäisessä versiossa käytetään vain GitHub Actionsia.
