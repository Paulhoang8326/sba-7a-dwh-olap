"""Retrospective resolved-loan baseline, NOT a historical deployment backtest."""
import json
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, confusion_matrix, precision_score, recall_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
NUM = ['GrossApproval','SBAGuaranteedApproval','InitialInterestRate','TermInMonths']
CAT = ['ProcessingMethod','FixedorVariableInterestInd','SectorCode','StateCode','BusinessType','BusinessAge']


def main():
    d = pd.read_csv(ROOT / 'data/processed/mining_resolved.csv', dtype={c:str for c in CAT})
    # Older approval cohorts have longer outcome observation. End all data at FY2023.
    train = d[d.ApprovalDate.lt('2021-10-01')].copy()
    valid = d[d.ApprovalDate.ge('2021-10-01') & d.ApprovalDate.lt('2022-10-01')].copy()
    test = d[d.ApprovalDate.ge('2022-10-01') & d.ApprovalDate.lt('2023-10-01')].copy()
    valid = valid[~valid.BorrowerGroup.isin(train.BorrowerGroup)]
    test = test[~test.BorrowerGroup.isin(pd.concat([train.BorrowerGroup, valid.BorrowerGroup]))]
    for split in [train, valid, test]:
        if split.ClassChargeOff.nunique() != 2:
            raise ValueError('Both classes required in each cohort.')
    numeric = Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())])
    categorical = Pipeline([('impute',SimpleImputer(strategy='most_frequent')),
                            ('encode',OneHotEncoder(handle_unknown='ignore'))])
    result = {'interpretation':'Retrospective classification among resolved loans only; snapshot outcome labels may postdate split boundaries. Not a prospective default model.',
              'splits':{n:{'rows':len(s),'positive_rate':float(s.ClassChargeOff.mean())} for n,s in [('train',train),('validation',valid),('test',test)]},'models':{}}
    candidates = {}
    for name, model in [('dummy',DummyClassifier(strategy='prior')),
                        ('logistic',LogisticRegression(max_iter=1000,class_weight='balanced',random_state=42)),
                        ('tree',DecisionTreeClassifier(max_depth=6,min_samples_leaf=100,class_weight='balanced',random_state=42))]:
        prep = ColumnTransformer([('num',numeric,NUM),('cat',categorical,CAT)])
        pipeline = Pipeline([('prepare',prep),('model',model)])
        pipeline.fit(train[NUM+CAT],train.ClassChargeOff)
        score = pipeline.predict_proba(valid[NUM+CAT])[:,1]
        result['models'][name] = {'validation_average_precision':float(average_precision_score(valid.ClassChargeOff,score))}
        candidates[name] = pipeline
    best = max(result['models'],key=lambda n:result['models'][n]['validation_average_precision'])
    score = candidates[best].predict_proba(test[NUM+CAT])[:,1]
    pred = score >= .5
    y = test.ClassChargeOff
    result['selected_model'] = best
    result['test'] = {'threshold':.5,'average_precision':float(average_precision_score(y,score)),
        'roc_auc':float(roc_auc_score(y,score)), 'precision':float(precision_score(y,pred,zero_division=0)),
        'recall':float(recall_score(y,pred)), 'f1':float(f1_score(y,pred)), 'confusion_matrix':confusion_matrix(y,pred).tolist()}
    target=ROOT/'docs/mining_baseline.json'
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
