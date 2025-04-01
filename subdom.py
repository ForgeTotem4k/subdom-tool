import socket
import requests
import concurrent.futures
from urllib.parse import urlparse

def load_subdomain_prefixes(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def check_subdomain(subdomain):
    try:
        socket.gethostbyname(subdomain)
        try:
            for protocol in ['https://', 'http://']:
                try:
                    response = requests.get(
                        f"{protocol}{subdomain}",
                        timeout=3,
                        allow_redirects=True,
                        headers={'User-Agent': 'Mozilla/5.0'},
                        verify=False
                    )
                    if response.status_code < 400:
                        final_url = response.url
                        if subdomain in final_url.replace('https://', '').replace('http://', '').split('/')[0]:
                            return True, None, protocol.strip(':/')
                        else:
                            return True, final_url, protocol.strip(':/')
                except:
                    continue
        except:
            pass
    except:
        pass
    return False, None, None

def find_active_subdomains(domain, prefixes):
    active = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_subdomain, f"{prefix}.{domain}"): prefix for prefix in prefixes}
        
        for future in concurrent.futures.as_completed(futures):
            prefix = futures[future]
            subdomain = f"{prefix}.{domain}"
            try:
                is_active, redirect, protocol = future.result()
                if is_active:
                    if redirect:
                        active[subdomain] = f"{protocol} → {redirect}"
                        print(f"⚠️ Редирект: {protocol}://{subdomain.ljust(30)} → {redirect}")
                    else:
                        active[subdomain] = f"Активен ({protocol})"
                        print(f"✅ Найден: {protocol}://{subdomain}")
                else:
                    print(f"❌ Недоступен: {subdomain}")
            except:
                print(f"❌ Ошибка проверки: {subdomain}")
    
    return active

def main():
    print("Поиск активных поддоменов")
    domain = input("Введите домен (например, vk.ru): ").strip()
    prefix_file = input("Введите имя файла с префиксами (по умолчанию subdomain_prefixes.txt): ").strip() or "subdomain_prefixes.txt"
    
    parsed = urlparse(domain if '://' in domain else f'//{domain}')
    domain = parsed.netloc or parsed.path.split('/')[0]
    
    try:
        prefixes = load_subdomain_prefixes(prefix_file)
        print(f"\nПроверяю {len(prefixes)} поддоменов для {domain}...\n")
        
        active = find_active_subdomains(domain, prefixes)
        
        print("\nРезультаты:")
        for subdomain, status in active.items():
            print(f"{subdomain.ljust(30)} {status}")
            
    except FileNotFoundError:
        print(f"\nОшибка: файл '{prefix_file}' не найден")
        print("Создайте файл с префиксами (каждый на новой строке)")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    main()
