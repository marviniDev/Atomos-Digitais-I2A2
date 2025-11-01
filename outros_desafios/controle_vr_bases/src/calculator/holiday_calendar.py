"""
Módulo para gerenciar calendário de feriados
"""
import logging
from datetime import datetime, date
from typing import List, Dict, Set
import calendar

logger = logging.getLogger(__name__)

class HolidayCalendar:
    """Classe para gerenciar feriados nacionais, estaduais e municipais"""
    
    def __init__(self):
        self.national_holidays = self._get_national_holidays()
        self.state_holidays = self._get_state_holidays()
        self.municipal_holidays = self._get_municipal_holidays()
    
    def _get_national_holidays(self) -> Dict[int, List[date]]:
        """Retorna feriados nacionais por ano"""
        holidays = {}
        
        for year in range(2020, 2030):  # 10 anos de feriados
            year_holidays = [
                date(year, 1, 1),    # Confraternização Universal
                date(year, 4, 21),   # Tiradentes
                date(year, 5, 1),    # Dia do Trabalhador
                date(year, 9, 7),    # Independência do Brasil
                date(year, 10, 12),  # Nossa Senhora Aparecida
                date(year, 11, 2),   # Finados
                date(year, 11, 15),  # Proclamação da República
                date(year, 12, 25),  # Natal
            ]
            
            # Adicionar Páscoa (feriado móvel)
            easter = self._calculate_easter(year)
            from datetime import timedelta
            year_holidays.extend([
                easter - timedelta(days=2),  # Sexta-feira Santa
                easter,                      # Páscoa
            ])
            
            # Adicionar Carnaval (feriado móvel)
            carnival = easter - timedelta(days=47)  # 47 dias antes da Páscoa
            year_holidays.extend([
                carnival,                    # Carnaval
                carnival + timedelta(days=1),  # Carnaval (segunda)
            ])
            
            holidays[year] = year_holidays
        
        return holidays
    
    def _get_state_holidays(self) -> Dict[str, Dict[int, List[date]]]:
        """Retorna feriados estaduais por estado e ano"""
        holidays = {}
        
        # Feriados de SP
        holidays['SP'] = {}
        for year in range(2020, 2030):
            holidays['SP'][year] = [
                date(year, 7, 9),    # Revolução Constitucionalista
            ]
        
        # Feriados de RJ
        holidays['RJ'] = {}
        for year in range(2020, 2030):
            holidays['RJ'][year] = [
                date(year, 4, 23),   # São Jorge
                date(year, 10, 2),   # Aniversário do RJ
            ]
        
        # Feriados de RS
        holidays['RS'] = {}
        for year in range(2020, 2030):
            holidays['RS'][year] = [
                date(year, 9, 20),   # Revolução Farroupilha
            ]
        
        # Feriados de PR
        holidays['PR'] = {}
        for year in range(2020, 2030):
            holidays['PR'][year] = [
                date(year, 12, 19),  # Emancipação do Paraná
            ]
        
        return holidays
    
    def _get_municipal_holidays(self) -> Dict[str, Dict[int, List[date]]]:
        """Retorna feriados municipais por cidade e ano"""
        holidays = {}
        
        # Feriados de São Paulo
        holidays['São Paulo'] = {}
        for year in range(2020, 2030):
            holidays['São Paulo'][year] = [
                date(year, 1, 25),   # Aniversário de São Paulo
            ]
        
        # Feriados de Rio de Janeiro
        holidays['Rio de Janeiro'] = {}
        for year in range(2020, 2030):
            holidays['Rio de Janeiro'][year] = [
                date(year, 3, 1),    # Aniversário do Rio
            ]
        
        # Feriados de Porto Alegre
        holidays['Porto Alegre'] = {}
        for year in range(2020, 2030):
            holidays['Porto Alegre'][year] = [
                date(year, 3, 26),   # Aniversário de Porto Alegre
            ]
        
        # Feriados de Curitiba
        holidays['Curitiba'] = {}
        for year in range(2020, 2030):
            holidays['Curitiba'][year] = [
                date(year, 3, 29),   # Aniversário de Curitiba
            ]
        
        return holidays
    
    def _calculate_easter(self, year: int) -> date:
        """Calcula a data da Páscoa para um ano específico"""
        # Algoritmo de Gauss para calcular a Páscoa
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = (h + l - 7 * m + 114) // 31
        p = (h + l - 7 * m + 114) % 31
        
        return date(year, n, p + 1)
    
    def get_holidays_for_month(self, year: int, month: int, state: str = None, city: str = None) -> List[date]:
        """
        Retorna todos os feriados de um mês específico
        
        Args:
            year: Ano
            month: Mês
            state: Estado (opcional)
            city: Cidade (opcional)
            
        Returns:
            List[date]: Lista de feriados
        """
        holidays = []
        
        # Adicionar feriados nacionais
        if year in self.national_holidays:
            for holiday in self.national_holidays[year]:
                if holiday.month == month:
                    holidays.append(holiday)
        
        # Adicionar feriados estaduais
        if state and state in self.state_holidays and year in self.state_holidays[state]:
            for holiday in self.state_holidays[state][year]:
                if holiday.month == month:
                    holidays.append(holiday)
        
        # Adicionar feriados municipais
        if city and city in self.municipal_holidays and year in self.municipal_holidays[city]:
            for holiday in self.municipal_holidays[city][year]:
                if holiday.month == month:
                    holidays.append(holiday)
        
        return sorted(holidays)
    
    def is_holiday(self, check_date: date, state: str = None, city: str = None) -> bool:
        """
        Verifica se uma data é feriado
        
        Args:
            check_date: Data a verificar
            state: Estado (opcional)
            city: Cidade (opcional)
            
        Returns:
            bool: True se for feriado
        """
        holidays = self.get_holidays_for_month(
            check_date.year, 
            check_date.month, 
            state, 
            city
        )
        return check_date in holidays
    
    def get_working_days_in_month(self, year: int, month: int, state: str = None, city: str = None) -> int:
        """
        Calcula o número de dias úteis em um mês
        
        Args:
            year: Ano
            month: Mês
            state: Estado (opcional)
            city: Cidade (opcional)
            
        Returns:
            int: Número de dias úteis
        """
        # Obter todos os dias do mês
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Contar dias úteis (excluir fins de semana e feriados)
        working_days = 0
        holidays = self.get_holidays_for_month(year, month, state, city)
        
        for day in range(1, days_in_month + 1):
            check_date = date(year, month, day)
            
            # Verificar se é fim de semana
            if check_date.weekday() >= 5:  # Sábado = 5, Domingo = 6
                continue
            
            # Verificar se é feriado
            if check_date in holidays:
                continue
            
            working_days += 1
        
        return working_days
    
    def get_holiday_info(self, year: int, month: int, state: str = None, city: str = None) -> Dict[str, any]:
        """
        Retorna informações detalhadas sobre feriados de um mês
        
        Args:
            year: Ano
            month: Mês
            state: Estado (opcional)
            city: Cidade (opcional)
            
        Returns:
            Dict: Informações sobre feriados
        """
        holidays = self.get_holidays_for_month(year, month, state, city)
        working_days = self.get_working_days_in_month(year, month, state, city)
        total_days = calendar.monthrange(year, month)[1]
        
        return {
            'year': year,
            'month': month,
            'state': state,
            'city': city,
            'total_days': total_days,
            'working_days': working_days,
            'holidays': holidays,
            'holiday_count': len(holidays),
            'weekend_days': total_days - working_days - len(holidays)
        }
