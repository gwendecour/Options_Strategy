import numpy as np
from scipy.stats import norm
from src.derivatives.instruments import FinancialInstrument

class EuropeanOption(FinancialInstrument):
    
    def __init__(self, **kwargs):
        """
        Initializes a Vanilla European Option.
        """
        super().__init__(**kwargs)
        
        self.S = float(kwargs.get('S'))
        self.K = float(kwargs.get('K'))
        self.T = float(kwargs.get('T'))
        self.r = float(kwargs.get('r'))
        self.sigma = float(kwargs.get('sigma'))
        self.q = float(kwargs.get('q', 0.0)) 
        self.option_type = kwargs.get('option_type', 'call').lower()

    def _d1(self):
        return (np.log(self.S/self.K) + (self.r - self.q + 0.5 * self.sigma**2) * self.T) / (self.sigma * np.sqrt(self.T))

    def _d2(self):
        return self._d1() - self.sigma * np.sqrt(self.T)

    def price(self):
        d1 = self._d1()
        d2 = self._d2()
        
        if self.option_type == "call":
            return self.S * np.exp(-self.q * self.T) * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:
            return self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S * np.exp(-self.q * self.T) * norm.cdf(-d1)
        
    def greeks(self):
        return {
            "delta": self.delta(),
            "gamma": self.gamma(),
            "vega": self.vega_point(),
            "theta": self.daily_theta()
        }

    def delta(self):
        if self.option_type == "call":
            return np.exp(-self.q * self.T) * norm.cdf(self._d1())
        else:
            return -np.exp(-self.q * self.T) * norm.cdf(-self._d1())

    def gamma(self):
        return np.exp(-self.q * self.T) * norm.pdf(self._d1()) / (self.S * self.sigma * np.sqrt(self.T))

    def vega_point(self):
        return (self.S * np.exp(-self.q * self.T) * norm.pdf(self._d1()) * np.sqrt(self.T)) / 100

    def daily_theta(self):
        d1 = self._d1()
        d2 = self._d2()
        common = -(self.S * np.exp(-self.q * self.T) * norm.pdf(d1) * self.sigma) / (2 * np.sqrt(self.T))
        
        if self.option_type == "call":
            theta = common - self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(d2) + self.q * self.S * np.exp(-self.q * self.T) * norm.cdf(d1)
        else:
            theta = common + self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.q * self.S * np.exp(-self.q * self.T) * norm.cdf(-d1)
            
        return theta / 365

class Stock(FinancialInstrument):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.S = float(kwargs.get('S', 100.0))
        self.K = None # Not applicable for stock
        self.option_type = "stock"
        
    def price(self):
        return self.S
        
    def greeks(self):
        return {
            "delta": 1.0,
            "gamma": 0.0,
            "vega": 0.0,
            "theta": 0.0
        }
    
    def delta(self): return 1.0
    def gamma(self): return 0.0
    def vega_point(self): return 0.0
    def daily_theta(self): return 0.0

