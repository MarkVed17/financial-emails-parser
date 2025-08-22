from typing import List, Dict, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import calendar

class AnalyticsService:
    def __init__(self):
        pass
    
    def generate_comprehensive_insights(self, extracted_data: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive financial insights from extracted email data"""
        
        try:
            # Filter relevant data
            relevant_data = [item for item in extracted_data if item.get('is_relevant', False)]
            
            insights = {
                "spending_analysis": self._analyze_spending(relevant_data),
                "income_analysis": self._analyze_income(relevant_data),
                "subscription_analysis": self._analyze_subscriptions(relevant_data),
                "travel_analysis": self._analyze_travel(relevant_data),
                "bills_analysis": self._analyze_bills(relevant_data),
                "investment_analysis": self._analyze_investments(relevant_data),
                "financial_health": self._calculate_financial_health(relevant_data),
                "summary": self._generate_summary(relevant_data)
            }
            
            return insights
        except Exception as e:
            print(f"Error generating insights: {e}")
            # Return default structure
            return {
                "spending_analysis": {"total_spending": 0, "category_breakdown": {}, "monthly_trend": {}, "top_merchants": {}, "average_monthly_spending": 0, "highest_single_transaction": 0},
                "income_analysis": {"total_income": 0, "employers": [], "pay_cycles": {}, "monthly_income_trend": {}, "average_monthly_income": 0},
                "subscription_analysis": {"active_subscriptions": 0, "monthly_recurring_cost": 0, "services": [], "total_annual_cost": 0},
                "travel_analysis": {"total_trips": 0, "preferred_airlines": [], "preferred_hotels": []},
                "bills_analysis": {"total_bills": 0, "monthly_bill_amount": 0, "utility_breakdown": {}},
                "investment_analysis": {"total_investments": 0, "platforms": [], "instruments": {}},
                "financial_health": {"savings_rate": 0, "subscription_to_spending_ratio": 0, "financial_health_score": 50, "monthly_surplus_deficit": 0},
                "summary": {"total_emails_analyzed": len(extracted_data), "financial_emails_found": 0, "transactions_extracted": 0, "income_entries_found": 0, "subscriptions_identified": 0, "analysis_date": "2025-08-20"}
            }
    
    def _analyze_spending(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze spending patterns"""
        try:
            transactions = [item['transaction'] for item in data if item.get('transaction')]
            expenses = [t for t in transactions if t and t.get('transaction_type') == 'expense' and t.get('amount')]
            
            if not expenses:
                return {"total_spending": 0, "category_breakdown": {}, "monthly_trend": {}, "top_merchants": {}, "average_monthly_spending": 0, "highest_single_transaction": 0}
            
            # Category-wise spending
            category_spending = defaultdict(float)
            monthly_spending = defaultdict(float)
            merchant_spending = defaultdict(float)
            
            for expense in expenses:
                amount = expense.get('amount', 0)
                category = expense.get('category', 'Other')
                merchant = expense.get('merchant', 'Unknown')
                date_str = expense.get('date', '')
                
                category_spending[category] += amount
                merchant_spending[merchant] += amount
                
                if date_str:
                    try:
                        month_key = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m')
                        monthly_spending[month_key] += amount
                    except ValueError:
                        pass
            
            # Top merchants
            top_merchants = dict(sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Calculate average monthly spending
            if monthly_spending:
                avg_monthly = sum(monthly_spending.values()) / len(monthly_spending)
            else:
                avg_monthly = 0
            
            return {
                "total_spending": sum(expense.get('amount', 0) for expense in expenses),
                "category_breakdown": dict(category_spending),
                "monthly_trend": dict(monthly_spending),
                "top_merchants": top_merchants,
                "average_monthly_spending": round(avg_monthly, 2),
                "highest_single_transaction": max((e.get('amount', 0) for e in expenses), default=0)
            }
        except Exception as e:
            print(f"Error in spending analysis: {e}")
            return {"total_spending": 0, "category_breakdown": {}, "monthly_trend": {}, "top_merchants": {}, "average_monthly_spending": 0, "highest_single_transaction": 0}
    
    def _analyze_income(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze income patterns"""
        try:
            income_data = [item['income'] for item in data if item.get('income')]
            
            if not income_data:
                return {"total_income": 0, "employers": [], "pay_cycles": {}, "monthly_income_trend": {}, "average_monthly_income": 0}
            
            employers = list(set(inc.get('employer') for inc in income_data if inc.get('employer')))
            pay_cycles = Counter(inc.get('pay_cycle') for inc in income_data if inc.get('pay_cycle'))
            
            total_income = sum(inc.get('amount', 0) for inc in income_data)
            monthly_income = defaultdict(float)
            
            for inc in income_data:
                date_str = inc.get('date', '')
                if date_str:
                    try:
                        month_key = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m')
                        monthly_income[month_key] += inc.get('amount', 0)
                    except ValueError:
                        pass
            
            avg_monthly_income = sum(monthly_income.values()) / len(monthly_income) if monthly_income else 0
            
            return {
                "total_income": total_income,
                "employers": employers,
                "pay_cycles": dict(pay_cycles),
                "monthly_income_trend": dict(monthly_income),
                "average_monthly_income": round(avg_monthly_income, 2)
            }
        except Exception as e:
            print(f"Error in income analysis: {e}")
            return {"total_income": 0, "employers": [], "pay_cycles": {}, "monthly_income_trend": {}, "average_monthly_income": 0}
    
    def _analyze_subscriptions(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze subscription patterns"""
        subscriptions = [item['subscription'] for item in data if item.get('subscription')]
        
        if not subscriptions:
            return {"active_subscriptions": 0, "monthly_recurring_cost": 0, "services": []}
        
        services = []
        monthly_cost = 0
        
        for sub in subscriptions:
            service_info = {
                "service": sub.get('service'),
                "amount": sub.get('amount', 0),
                "billing_cycle": sub.get('billing_cycle'),
                "next_billing": sub.get('next_billing')
            }
            services.append(service_info)
            
            # Convert to monthly cost
            amount = sub.get('amount', 0)
            cycle = sub.get('billing_cycle', 'monthly')
            
            if cycle == 'yearly':
                monthly_cost += amount / 12
            elif cycle == 'monthly':
                monthly_cost += amount
            elif cycle == 'weekly':
                monthly_cost += amount * 4.33
        
        return {
            "active_subscriptions": len(subscriptions),
            "monthly_recurring_cost": round(monthly_cost, 2),
            "services": services,
            "total_annual_cost": round(monthly_cost * 12, 2)
        }
    
    def _analyze_travel(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze travel patterns"""
        travel_data = [item['travel'] for item in data if item.get('travel')]
        
        if not travel_data:
            return {"total_trips": 0, "preferred_airlines": [], "preferred_hotels": []}
        
        airlines = [t.get('airline') for t in travel_data if t.get('airline')]
        hotels = [t.get('hotel') for t in travel_data if t.get('hotel')]
        destinations = [t.get('destination') for t in travel_data if t.get('destination')]
        
        airline_frequency = Counter(airlines)
        hotel_frequency = Counter(hotels)
        destination_frequency = Counter(destinations)
        
        total_travel_spend = sum(t.get('booking_amount', 0) for t in travel_data)
        
        return {
            "total_trips": len(travel_data),
            "total_travel_spending": total_travel_spend,
            "preferred_airlines": dict(airline_frequency.most_common(5)),
            "preferred_hotels": dict(hotel_frequency.most_common(5)),
            "popular_destinations": dict(destination_frequency.most_common(10)),
            "average_trip_cost": round(total_travel_spend / len(travel_data), 2) if travel_data else 0
        }
    
    def _analyze_bills(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze bills and utilities"""
        bills_data = [item['bills'] for item in data if item.get('bills')]
        
        if not bills_data:
            return {"total_bills": 0, "monthly_bill_amount": 0, "utility_breakdown": {}}
        
        utility_spending = defaultdict(float)
        providers = set()
        
        for bill in bills_data:
            utility_type = bill.get('utility_type', 'Other')
            amount = bill.get('amount', 0)
            provider = bill.get('provider')
            
            utility_spending[utility_type] += amount
            if provider:
                providers.add(provider)
        
        total_bills = sum(utility_spending.values())
        
        return {
            "total_bills": len(bills_data),
            "monthly_bill_amount": round(total_bills, 2),
            "utility_breakdown": dict(utility_spending),
            "service_providers": list(providers)
        }
    
    def _analyze_investments(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze investment patterns"""
        investment_data = [item['investment'] for item in data if item.get('investment')]
        
        if not investment_data:
            return {"total_investments": 0, "platforms": [], "instruments": {}}
        
        platforms = list(set(inv.get('platform') for inv in investment_data if inv.get('platform')))
        instruments = Counter(inv.get('instrument') for inv in investment_data if inv.get('instrument'))
        
        investment_amount = sum(inv.get('amount', 0) for inv in investment_data if inv.get('action') == 'buy')
        withdrawal_amount = sum(inv.get('amount', 0) for inv in investment_data if inv.get('action') == 'sell')
        
        return {
            "total_investments": len(investment_data),
            "investment_platforms": platforms,
            "instrument_breakdown": dict(instruments),
            "total_invested": investment_amount,
            "total_withdrawn": withdrawal_amount,
            "net_investment": investment_amount - withdrawal_amount
        }
    
    def _calculate_financial_health(self, data: List[Dict]) -> Dict[str, Any]:
        """Calculate financial health metrics"""
        
        # Get spending and income
        spending_analysis = self._analyze_spending(data)
        income_analysis = self._analyze_income(data)
        subscription_analysis = self._analyze_subscriptions(data)
        
        avg_monthly_spending = spending_analysis.get('average_monthly_spending', 0)
        avg_monthly_income = income_analysis.get('average_monthly_income', 0)
        monthly_subscriptions = subscription_analysis.get('monthly_recurring_cost', 0)
        
        # Calculate metrics
        savings_rate = 0
        if avg_monthly_income > 0:
            savings_rate = ((avg_monthly_income - avg_monthly_spending) / avg_monthly_income) * 100
        
        subscription_ratio = 0
        if avg_monthly_spending > 0:
            subscription_ratio = (monthly_subscriptions / avg_monthly_spending) * 100
        
        # Financial health score (0-100)
        health_score = 50  # Base score
        
        if savings_rate > 20:
            health_score += 20
        elif savings_rate > 10:
            health_score += 10
        elif savings_rate < 0:
            health_score -= 20
        
        if subscription_ratio < 10:
            health_score += 10
        elif subscription_ratio > 25:
            health_score -= 10
        
        health_score = max(0, min(100, health_score))
        
        return {
            "savings_rate": round(savings_rate, 1),
            "subscription_to_spending_ratio": round(subscription_ratio, 1),
            "financial_health_score": health_score,
            "monthly_surplus_deficit": round(avg_monthly_income - avg_monthly_spending, 2)
        }
    
    def _generate_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """Generate executive summary"""
        
        total_emails_analyzed = len(data)
        financial_emails = len([d for d in data if d.get('is_relevant')])
        
        transactions = len([d for d in data if d.get('transaction')])
        income_entries = len([d for d in data if d.get('income')])
        subscriptions = len([d for d in data if d.get('subscription')])
        
        return {
            "total_emails_analyzed": total_emails_analyzed,
            "financial_emails_found": financial_emails,
            "transactions_extracted": transactions,
            "income_entries_found": income_entries,
            "subscriptions_identified": subscriptions,
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }