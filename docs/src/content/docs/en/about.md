---
title: About MABIMS.dev
description: Free open-source API for the Indonesian Hijri calendar based on official MABIMS data from Kementerian Agama RI.
---

## What is MABIMS.dev?

MABIMS.dev is a free open-source API that provides an ecosystem for the Indonesian Hijri calendar. It uses official MABIMS data published by Indonesia's Ministry of Religious Affairs (Kementerian Agama RI), not Umm al-Qura (Saudi Arabia's standard).

## Who is it for?

- **Developers** building web or mobile apps with Hijri calendar features
- **Mosque and pesantren apps** that need to display fasting start, Eid al-Fitr, and Eid al-Adha dates matching Kemenag announcements
- **Islamic schools and universities** integrating Hijri dates into academic systems
- **Anyone** who needs accurate Indonesian Hijri dates

## Why MABIMS, Not Umm al-Qura?

Almost all Hijri calendar APIs and libraries default to Umm al-Qura. Umm al-Qura is Saudi Arabia's official calendar, designed for their needs — not Indonesia's.

Because the rukyah method and observation location differ, results can be ±1 day off from Kemenag's official decisions — especially for Ramadan start, Eid al-Fitr, and Eid al-Adha. MABIMS.dev uses public Kemenag RI table data and Neo MABIMS criteria (moon altitude ≥ 3°, elongation ≥ 6.4° at Sabang sunset) for dates beyond table coverage.

## Compared to Alternatives

For the Indonesian context, MABIMS.dev is more accurate than Umm al-Qura (Saudi standard, ±1 day off) and Aladhan API (which also defaults to Umm al-Qura). MABIMS.dev uses official Kemenag RI data, not data from another country's authority.

If you're currently using the Aladhan API, see the [Migration from Aladhan](/en/migration) guide for response format comparison and migration code examples.

## Repository

Source code is available at [github.com/PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api). Contributions are welcome via pull request.

## License

MABIMS.dev is licensed under the [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).

## Contact

For questions, technical support, or commercial partnerships:
- Email: [halo@pixostudio.id](mailto:halo@pixostudio.id)
- GitHub: [PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api)
