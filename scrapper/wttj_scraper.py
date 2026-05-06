import os
import asyncio
from typing import List, Dict, AsyncGenerator
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from base_scraper import JobScraper

# --- env configuration ---
root_dir = Path(__file__).resolve().parent 
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

class WttjScraper(JobScraper):
    """
    Scraper Asynchrone pour Welcome to the Jungle.
    Utilise asyncio.gather pour scraper les descriptions en parallèle (par rafales de 10 max).
    """
    
    URL_HOME = "https://www.welcometothejungle.com/fr/jobs"
    URL_MATCHES = "https://www.welcometothejungle.com/fr/jobs-matches"
    
    SEL_COOKIE_BTN = "#axeptio_btn_acceptAll"
    SEL_LOGIN_INDICATOR = 'button:has-text("Se connecter"), a:has-text("Se connecter")'
    SEL_ROLE_ACCORDION = 'button:has-text("Rôle")'
    SEL_ROLE_INPUT = 'input[name="futureRole"]'
    SEL_SAVE_FILTERS_BTN = '[data-testid="filters-save-button"]'
    SEL_JOB_CARD = 'a[href*="/companies/"][href*="/jobs/"]'
    SEL_NEXT_PAGE_BTN = '[data-testid="job-list-pagination-arrow-next"]'
    SEL_JOB_DETAILS = '#the-position-section'

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.profile_dir = self._get_profile_directory()

    def _get_profile_directory(self) -> str:
        env_profile_dir = os.getenv('WTTJ_PROFILE_DIR')
        if env_profile_dir:
            return str(root_dir / env_profile_dir)
        return str(root_dir / "wttj_chrome_profile")

    async def _handle_cookies(self, page: Page) -> None:
        print("-> Vérification des cookies...")
        try:
            cookie_btn = page.locator(self.SEL_COOKIE_BTN)
            await cookie_btn.wait_for(state="visible", timeout=3000)
            await cookie_btn.click(force=True)
            print("   => Cookies acceptés.")
        except PlaywrightTimeoutError:
            print("   => Pas de bannière de cookies détectée.")

    async def _check_authentication(self, page: Page) -> bool:
        print("-> Vérification de l'état de connexion...")
        login_indicator = page.locator(self.SEL_LOGIN_INDICATOR).first
        
        if await login_indicator.is_visible():
            print("\n LE BOT N'EST PAS CONNECTÉ ! ")
            if self.headless:
                print(" ERREUR: Le navigateur est invisible (headless=True).")
                print(" Relance avec 'headless=False' pour pouvoir te connecter.")
                return False
            else:
                print(" Connecte-toi manuellement. Le bot attend que le bouton 'Se connecter' disparaisse...")
                await login_indicator.wait_for(state="hidden", timeout=0)
                print("\n Connexion détectée ! Sauvegarde de la session...")
                await asyncio.sleep(3)
                return True
        else:
            print(" Bot déjà connecté via le profil sauvegardé.")
            return True

    async def _apply_search_filters(self, page: Page, keyword: str) -> bool:
        print(f"-> Navigation vers la page de Matching ({self.URL_MATCHES})...")
        await page.goto(self.URL_MATCHES, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        print("-> Application du filtre 'Rôle'...")
        try:
            role_button = page.locator(self.SEL_ROLE_ACCORDION).first
            if await role_button.is_visible() and await role_button.get_attribute("aria-expanded") == "false":
                await role_button.click(force=True)
                await asyncio.sleep(1)
        except Exception:
            pass

        search_input = page.locator(self.SEL_ROLE_INPUT)
        try:
            await search_input.wait_for(state="visible", timeout=10000)
            await search_input.click(force=True)
            await page.evaluate('el => el.value = ""', await search_input.element_handle())
            await page.keyboard.type(keyword, delay=50)
            print(f"   => '{keyword}' saisi avec succès.")
        except PlaywrightTimeoutError:
            print(" Impossible de trouver le champ 'Intitulé de poste'.")
            return False
        
        print("-> Clic sur 'Enregistrer'...")
        try:
            save_button = page.locator(self.SEL_SAVE_FILTERS_BTN)
            await save_button.wait_for(state="visible", timeout=3000)
            await save_button.click(force=True)
        except PlaywrightTimeoutError:
            await page.keyboard.press("Enter")
            
        return True

    def _parse_job_description(self, html_content: str) -> str:
        """
        Extrait et formate le texte de la description détaillée d'une offre.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        position_section = soup.find(id="the-position-section")
        
        if not position_section:
            return "Section description introuvable dans le code source."
            
        # find_all va chercher toutes ces balises, peu importe leur niveau d'imbrication (nested)
        elements = position_section.find_all(['h3', 'h4', 'p', 'ul'])
        extracted_texts = []
        
        for el in elements:
            if el.name in ['h3', 'h4']:
                # On met les titres en majuscules avec un saut de ligne pour aérer
                extracted_texts.append(f"\n{el.get_text(strip=True).upper()}")
            elif el.name == 'ul':
                # On formate les listes à puces
                for li in el.find_all('li'):
                    extracted_texts.append(f"- {li.get_text(strip=True)}")
            elif el.name == 'p':
                text = el.get_text(strip=True)
                if text: # On ignore les paragraphes vides
                    extracted_texts.append(text)
                    
        return "\n".join(extracted_texts)
    
    async def _fetch_full_job(self, context, job_base: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """
        Ouvre un onglet, va sur l'URL de l'offre, délègue le parsing,
        formatte le dict pour SQL et referme l'onglet.
        """
        async with semaphore:
            new_page = await context.new_page()
            detail_text = ""
            
            try:
                # 1. Navigation Playwright
                await new_page.goto(job_base['url'], wait_until="domcontentloaded", timeout=15000)
                await new_page.wait_for_selector(self.SEL_JOB_DETAILS, timeout=10000)
                
                # 2. Récupération du HTML
                html_content = await new_page.content()
                
                # --- SÉPARATION DES PRÉOCCUPATIONS (SoC) ---
                # 3. Délégation du parsing à notre fonction pure
                detail_text = self._parse_job_description(html_content)
                
            except PlaywrightTimeoutError:
                detail_text = "Timeout : la page de l'offre a mis trop de temps à charger."
                print(f"  [Timeout] Échec sur l'URL : {job_base['url']}")
            except Exception as e:
                detail_text = f"Erreur d'extraction : {e}"
                print(f"  [Erreur] Sur l'URL {job_base['url']} : {e}")
            finally:
                await new_page.close()
            
            # --- FORMATAGE POUR SQL ---
            meta_tags = [job_base['location'], job_base['contract'], job_base['salary'], job_base['date']]
            clean_meta = " | ".join([m for m in meta_tags if m and m != 'N/A'])
            
            full_description = f"{clean_meta}\n\n{detail_text}" if clean_meta else detail_text

            return {
                'title': job_base['title'],
                'company': job_base['company'],
                'description': full_description,
                'url': job_base['url'],
                'date_posted': None 
            }

    async def _extract_all_pages(self, page: Page) -> AsyncGenerator[Dict, None]:
        print("\n Lancement de l'extraction asynchrone multi-pages...")
        seen_urls = set()
        page_num = 1
        context = page.context 
        
        # Limite stricte : 10 onglets ouverts en même temps maximum
        semaphore = asyncio.Semaphore(10)
        
        while True:
            print(f"\n--- Lecture de la page {page_num} ---")
            
            try:
                await page.wait_for_selector(self.SEL_JOB_CARD, timeout=15000)
                await asyncio.sleep(2) 
            except PlaywrightTimeoutError:
                print(" Timeout ou aucune offre trouvée sur cette page.")
                break
            
            html_content = await page.content()
            basic_jobs = self.parse_new_wttj_html(html_content)
            
            # 1. Préparation des tâches asynchrones pour cette page
            tasks = []
            for job in basic_jobs:
                if job['url'] not in seen_urls:
                    seen_urls.add(job['url'])
                    tasks.append(self._fetch_full_job(context, job, semaphore))
                    
            if not tasks and page_num > 1:
                print("   => Aucune nouvelle offre détectée (sécurité anti-boucle infinie).")
                break
            
            # 2. Exécution en rafale : On lance les X tâches en même temps !
            if tasks:
                print(f"   => Aspiration de {len(tasks)} descriptions en parallèle...")
                full_jobs = await asyncio.gather(*tasks)
                
                # 3. Streaming (yield) vers la base de données
                for fj in full_jobs:
                    yield fj

            # 4. Pagination
            try:
                next_btn = page.locator(self.SEL_NEXT_PAGE_BTN)
                if await next_btn.is_visible():
                    if await next_btn.is_disabled() or await next_btn.get_attribute('disabled') is not None:
                        print("   => Dernière page atteinte.")
                        break
                    
                    await next_btn.click(force=True)
                    page_num += 1
                    await asyncio.sleep(3) # Pause réseau pour charger la nouvelle page
                else:
                    print("   => Bouton 'Suivant' invisible. Fin de la pagination.")
                    break
            except Exception as e:
                print(f"   => Erreur lors de la pagination : {e}")
                break

    def parse_new_wttj_html(self, html_content: str) -> List[Dict]:
        """Extraction basique et ultra-rapide des cartes via BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs_data = []
        job_cards = soup.find_all('a', href=True)
        
        for card in job_cards:
            href = card['href']
            if '/companies/' not in href or '/jobs/' not in href:
                continue
                
            job_info = {
                'url': f"https://www.welcometothejungle.com{href}",
                'title': 'N/A', 'company': 'N/A', 'location': 'N/A',
                'contract': 'N/A', 'salary': 'N/A', 'date': 'N/A'
            }
            
            first_p = card.find('p')
            if first_p: job_info['title'] = first_p.get_text(strip=True)
                
            logo_img = card.find('img', alt=lambda x: x and 'logo' in x.lower())
            if logo_img: job_info['company'] = logo_img['alt'].lower().replace(' logo', '').title()
                
            for svg in card.find_all('svg'):
                use_tag = svg.find('use')
                if not use_tag: continue
                    
                icon_ref = use_tag.get('href', '')
                parent_text = svg.parent.get_text(strip=True)
                
                if '#map-marker-alt' in icon_ref: job_info['location'] = parent_text
                elif '#clipboard-notes' in icon_ref: job_info['contract'] = parent_text
                elif '#coins' in icon_ref: job_info['salary'] = parent_text
                elif '#calendar' in icon_ref: job_info['date'] = parent_text
                    
            jobs_data.append(job_info)
        return jobs_data

    async def fetch_jobs(self, keyword: str, location: str = "") -> AsyncGenerator[Dict, None]:
        print(f"\n=== Démarrage de la recherche pour '{keyword}' ===")
        
        async with async_playwright() as p:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=self.headless,
                slow_mo=0, # On veut de la vitesse maximale pour l'asynchrone
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"] 
            )
            
            page = browser_context.pages[0]
            
            try:
                await page.goto(self.URL_HOME, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                
                await self._handle_cookies(page)
                
                if not await self._check_authentication(page):
                    return
                    
                if not await self._apply_search_filters(page, keyword):
                    return
                print(page.url())
                # Le 'async for' relaie le stream de la sous-méthode vers le script principal
                async for job in self._extract_all_pages(page):
                    yield job
                
            except Exception as e: 
                print(f"Erreur globale inattendue: {e}")
            finally:
                await browser_context.close()