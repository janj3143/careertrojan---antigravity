import heroImage from 'figma:asset/f018d212d455fe79b0907064aaa740e4a1d757f0.png';

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Hero Section */}
      <div className="relative w-full h-64 bg-gradient-to-r from-blue-900 to-blue-700 overflow-hidden">
        <img 
          src={heroImage} 
          alt="Business technology" 
          className="w-full h-full object-cover opacity-60"
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white">
            <h1 className="text-4xl mb-2">📜 Services Agreement</h1>
            <p className="text-xl opacity-90">IntelliCV AI Platform</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="bg-white rounded-lg shadow-lg p-8 md:p-12">
          <h2 className="text-3xl mb-8 text-gray-800">📜 Recruitment Services Agreement</h2>

          {/* Agreement Overview */}
          <section className="mb-10">
            <h3 className="text-2xl mb-4 text-gray-800">Agreement Overview</h3>
            <p className="text-gray-700 mb-4">
              This agreement outlines the terms regarding recruitment fees should a Mentor or Mentee join the Mentor's company. 
              A fee of <strong>5% of the annual package</strong> will be charged upon successful engagement.
            </p>

            <h4 className="text-xl mb-3 text-gray-800">Fee Distribution</h4>
            <p className="text-gray-700 mb-2">The recruitment fee will be distributed as follows:</p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li><strong>25%</strong> to a charity of the <strong>User's</strong> choice</li>
              <li><strong>25%</strong> to a charity of the <strong>Mentor's</strong> choice</li>
              <li><strong>25%</strong> to a charity of the <strong>Portal's</strong> choice</li>
              <li><strong>25%</strong> retained to support <strong>Admin costs and future development</strong></li>
            </ul>
          </section>

          <hr className="my-8 border-gray-300" />

          {/* Terms and Conditions */}
          <section className="mb-10">
            <h3 className="text-2xl mb-4 text-gray-800">Terms and Conditions</h3>
            
            <div className="mb-6">
              <p className="mb-1"><strong>JOHNSTON VERE ASSOCIATES LIMITED</strong></p>
              <p className="text-gray-700"><strong>RECRUITMENT CONSULTANCY</strong></p>
            </div>

            {/* 1. Definitions */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">1. Definitions</h4>
              <ul className="space-y-3 text-gray-700">
                <li>
                  <strong>"Annual Remuneration"</strong> means the basic salary plus any bonuses, commission, benefits in kind or any other remuneration, any regional or other weighting allowances and/or any other taxable allowances and/or any other payments due to the Candidate in connection with the Engagement for a period of 12 months.
                </li>
                <li>
                  <strong>"the Candidate"</strong> means any person, partnership or corporate body introduced to the Client by the Company for an Engagement
                </li>
                <li>
                  <strong>"the Company"</strong> means Johnston Vere Associates Limited (09071421) of 20 Derby Street Ormskirk Lancashire L39 2BY, UK
                </li>
                <li>
                  <strong>"Contingency Search"</strong> means a search for a Candidate which is conducted by the Company on behalf of the Client without an agreed written Recruitment Proposal and defined fee structure and where a Contingency Fee will be payable upon engagement of a Candidate in accordance with Schedule 1
                </li>
                <li>
                  <strong>"the Client"</strong> means the person, partnership or corporate body to whom the Candidate is introduced including any person connected with such as defined in section 3 of the Employment Business Regulations 2003
                </li>
                <li>
                  <strong>"Engagement"</strong> means the employment, hire or other use, directly or indirectly and whether under a contract of service or for services or otherwise of the Candidate by or on behalf of the Client and shall be deemed to have occurred upon written acceptance of a Client's offer of employment by a Candidate
                </li>
                <li>
                  <strong>"Fee"</strong> means either a Contingency or Retained Fee
                </li>
                <li>
                  <strong>"Introduction"</strong> means:
                  <ul className="list-disc list-inside ml-6 mt-2 space-y-2">
                    <li>(i) the Client's interview of a Candidate in person or by telephone, following the Client's instruction to the Company to search for a Candidate; or</li>
                    <li>(ii) the passing to the Client of a curriculum vitae or other information which identifies the Candidate and which leads either directly or indirectly to an Engagement of that Candidate and irrespective of whether the Client had previous knowledge of the Candidate howsoever obtained; or</li>
                    <li>(iii) if the Client engages any employees of the Company.</li>
                  </ul>
                  <p className="mt-2">Such introduction is deemed to have been made irrespective of a change in position to the original position to which the interview was arranged or for which information on the Candidate was supplied</p>
                </li>
                <li>
                  <strong>"Recruitment Proposal"</strong> means the agreement between the Company and the Client relating to a Retained Search
                </li>
                <li>
                  <strong>"Retained Search"</strong> means a search for a Candidate which is conducted by the Company on behalf of the Client in accordance with an agreed written Recruitment Proposal and defined fee structure therein
                </li>
              </ul>
            </div>

            {/* 2. Contract */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">2. Contract</h4>
              <p className="text-gray-700 mb-3">These Terms constitute the entire contract between the Company and the Client and:</p>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>(a) are deemed to be accepted by the Client by virtue of an Introduction to, or the Engagement of a Candidate or the passing of any information about the Candidate to any third party following an Introduction, and;</li>
                <li>(b) unless otherwise agreed in writing by a Director of the Company, these Terms and Conditions prevail over any other terms of business or conditions put forward by the Client, and;</li>
                <li>(c) no variation or alteration to these Terms shall be valid unless agreed in writing between a Director of the Company and the Client and a copy of the varied terms is given to the Client stating the date on or after which such varied terms shall apply.</li>
              </ul>
            </div>

            {/* 3. Agreement */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">3. Agreement</h4>
              <p className="text-gray-700">
                The Client agrees that the Company can act on its behalf in seeking Candidates for an Engagement using such methods as are agreed with the Client and on these terms and conditions.
              </p>
            </div>

            {/* 4. Fees */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">4. Fees</h4>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>(a) If the Company is employed by the Client to carry out a Contingency Search then the Contingency Fee payable shall be calculated in accordance with Schedule 1 and a fee is payable for each Candidate engaged by the Client.</li>
                <li>(b) If the Company is employed by the Client to carry out a Retained Search then the Retained Fee payable shall be calculated in accordance with the 'Fee Structure' section of the Recruitment Proposal and Schedule 2.</li>
              </ul>
            </div>

            {/* 5. The Client agrees */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">5. The Client agrees</h4>
              <ul className="list-disc list-inside space-y-3 text-gray-700 ml-4">
                <li>
                  (a) To pay to the Company the Fee in the event the Candidate is directly or indirectly engaged or employed by the Client or any other person, partnership or corporate body within 12 months of the latest of:-
                  <ul className="list-disc list-inside ml-6 mt-2 space-y-1">
                    <li>i) the date of provision of identity of the Candidate to the Client as a direct or indirect result of an introduction by the Company and</li>
                    <li>ii) the date of the last interview between the Candidate and the Client</li>
                    <li>iii) the referral of the Candidate made by the Client to any person, partnership or corporation and</li>
                    <li>iv) the date of the contract made between the Client and the Candidate which arose from such provision.</li>
                  </ul>
                  <p className="mt-2">Unless the Client provides satisfactory evidence they have been in contact with a Candidate within the 4 weeks prior to the provision of their identity to the Client by the Company and that they have been actively considering them for the position concerned then the introduction shall be deemed to have been made by the Company and a Fee shall be payable by the Client to the Company. For the purposes of this clause the Company shall be sole arbiter as to what constitutes satisfactory evidence.</p>
                </li>
                <li>(b) To provide the Company with a copy of any offer of an Engagement immediately it is made to the Candidate</li>
                <li>(c) To notify the Company immediately an Engagement is accepted</li>
                <li>(d) To pay to the Company interest on any overdue payments in accordance with the Late Payment of Commercial Debts (Interest) Act 1998</li>
                <li>(e) To pay Value Added Tax on the Fee where due</li>
                <li>(f) To pay the Fee in sterling unless previously agreed in writing by a Director of the Company</li>
                <li>(g) To pay all legal costs, charges and expenses incurred by the Company recovering any debt on a full indemnity basis</li>
                <li>
                  (h) Not to employ or seek to employ any of the Company's member of staff but if any such member of staff accepts an Engagement within 3 months of leaving the employment of the Company then this shall be regarded as an Introduction and the Client shall be liable to pay to the Company a Fee equivalent to the greater of:
                  <ul className="list-disc list-inside ml-6 mt-2 space-y-1">
                    <li>i) 25% of the Annual Remuneration to paid by the Client to the member of staff, or;</li>
                    <li>ii) 25% of the Annual Remuneration paid by the Company to the member of staff in the year preceding the date of such Engagement.</li>
                  </ul>
                </li>
              </ul>
            </div>

            {/* 6. The Company agrees */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">6. The Company agrees</h4>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>(a) To endeavour to ensure the suitability of the Candidate but the Client shall nevertheless satisfy himself as to the suitability of the Candidate and shall be responsible for taking up references, obtaining work permits and carrying out any necessary medical examinations</li>
                <li>(b) To ensure that the Candidate is aware of any requirements to be satisfied in respect of the Engagement</li>
              </ul>
            </div>

            {/* 7. Liability */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">7. Liability</h4>
              <p className="text-gray-700">
                The Company shall not be liable to the Client for any loss, injury, damage, expense or delay whatsoever incurred or suffered by the client arising from or in any way connected with the Company seeking the Candidate for the Client or the introduction by the Company to the Client of any Candidate or the Engagement of any Candidate by the Client
              </p>
            </div>

            {/* 8. Applicable Law */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">8. Applicable Law</h4>
              <p className="text-gray-700">
                The construction, validity and performance of these terms is governed by the law of England and the parties accept the jurisdiction of the English Courts
              </p>
            </div>

            {/* 9. Waiver */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">9. Waiver</h4>
              <p className="text-gray-700">
                No time or indulgence granted by the Company shall operate as a waiver of the Company's rights hereunder
              </p>
            </div>

            {/* 10. Confidentiality */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">10. Confidentiality</h4>
              <p className="text-gray-700">
                Each of the parties undertake to the other to keep confidential all information concerning the business and affairs of the other which it has obtained or received as a result of discussions leading up to the entering into this agreement or which it subsequently obtains during the course of this agreement and these obligations shall continue after the termination or expiry of the contract
              </p>
            </div>

            {/* 11. Invalidity */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">11. Invalidity</h4>
              <p className="text-gray-700">
                If any provision of this contract is deemed by a judicial or other competent authority to be void, voidable or illegal or otherwise unenforceable the remaining provisions of this contract shall remain in full force and effect
              </p>
            </div>
          </section>

          <hr className="my-8 border-gray-300" />

          {/* Schedule 1 */}
          <section className="mb-10">
            <h3 className="text-2xl mb-4 text-gray-800">Schedule 1: Contingency Placement Fees</h3>

            {/* 1. The Contingency Fee */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">1. The Contingency Fee</h4>
              <p className="text-gray-700 mb-3">
                If the Client has not instructed the Company to carry out a Retained Search then the Client will pay to the Company a 'Contingency Fee' for each Introduction resulting in an Engagement, as set out below:
              </p>
              <ul className="list-disc list-inside text-gray-700 ml-4">
                <li><strong>Fee:</strong> 5% of Annual Remuneration (as per platform agreement)</li>
              </ul>
            </div>

            {/* 2. Fixed Term Engagements */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">2. Fixed Term Engagements (Lasting less than 12 Months)</h4>
              <p className="text-gray-700 mb-3">In the event of the Engagement being for a period of less than 12 months:</p>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>a. the Fee payable to the Company shall be a monthly fee for the duration of the Engagement equivalent to 10% of the Candidate's gross monthly salary for that month, and;</li>
                <li>b. if the Engagement is extended beyond the initial fixed term or if the Client re-engages the Candidate within 12 calendar months from the date of termination of the first Engagement the Client shall be liable to pay a further fee for the subsequent period of Engagement, providing always that;</li>
                <li>c. should the total aggregate period of Engagement exceed 12 months then a full Contingency Fee will be payable.</li>
              </ul>
            </div>

            {/* 3. Payment Terms */}
            <div className="mb-8">
              <h4 className="text-xl mb-3 text-gray-800">3. Payment Terms</h4>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>a. For all services provided by the Company to the Client payment is due strictly 14 days from the date of the invoice date raised unless otherwise agreed in writing between the parties.</li>
                <li>b. The Contingency Fee becomes payable once the Candidate has provided written acceptance of the Client's offer of Engagement</li>
                <li>c. All fees are subject to Value Added Tax (VAT).</li>
                <li>d. In the event that any payments due to the Company become overdue, interest will be charged on all overdue balances in accordance with the Late Payment of Commercial Debts (Interest) Act 1998 from the first day that the invoice is overdue until the date payment is received in full. This will be calculated at the statutory interest rate (currently 8%) plus the Bank of England base rate. All legal costs, charges and expenses incurred by the Company recovering any debt shall be paid by the Client on a full indemnity basis.</li>
                <li>e. Where the amount of the actual Annual Remuneration is not known the Company will charge a Contingency Fee calculated on the minimum level of remuneration applicable for the position in which the Applicant has been engaged with regard to any information supplied to the Agency by the Client and/or comparable positions in the market generally for such positions</li>
              </ul>
            </div>
          </section>

          <hr className="my-8 border-gray-300" />

          {/* Footer Notice */}
          <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded">
            <p className="text-gray-800">
              <strong>ℹ️ Note:</strong> By using the Mentor Portal and engaging with Mentees, you acknowledge and agree to these terms.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
